# api/case_review.py
import os
import tempfile
import time
from datetime import datetime, timedelta
from typing import Optional

from docxtpl import DocxTemplate
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi import BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from .deps import get_current_active_user
from ..core.config import TEMPLATE_DIR
from ..core.logger import logger
from ..crud.case_review import list_cases_by_status, count_cases_by_status, update_review_status, \
    check_interest_conflict_for_case, get_case_approval_context, create_review_rejection_notifications
from ..database.database import get_db
from ..models.case import Case, CaseParty
from ..models.user import User
from ..schemas.case import CasePageOut, CaseSimpleOut, CaseOut, BatchReviewRequest
from ..utils.keywords_helper import determine_party_side, get_valid_keywords

router = APIRouter(
    prefix="/case_review",
    tags=["case_review"]
)


# --- 辅助函数：权限检查 ---
def check_review_permission(user: User):
    """
    检查用户是否有权审核案件
    逻辑：Role为Owner，或者 permissions['can_review_case'] 为 True
    """
    # 1. Owner 拥有最高权限
    if user.role == 'owner':
        return True

    # 2. 检查细粒度权限
    perms = user.permissions or {}
    if perms.get('can_review_case', False) is True:
        return True

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="您没有审核案件的权限")


# --- 辅助函数：纯内存利益冲突检测（专供批量审核使用） ---
def _pure_memory_conflict_check(case_id: int, global_case_cache: dict):
    """
    【核弹级优化核心】纯字典内存计算利益冲突，完全剥离数据库和 ORM 对象。
    运算速度极快，每次比对耗时小于 0.0001 秒。
    """
    current_case = global_case_cache.get(case_id)
    if not current_case:
        return {"has_conflict": False}

    current_parties = current_case["parties"]

    # 1. 提取本案委托人
    new_client_names = set()
    for p in current_parties:
        if "委托" in p["party_type"]:
            new_client_names.add(p["name"])
    if not new_client_names:
        return {"has_conflict": False, "details": []}

    # 2. 确定阵营
    client_side = "A"
    found_side = None
    has_side_b = False
    has_side_a = False

    for p in current_parties:
        p_name = p["name"]
        is_our_client = any(c in p_name or p_name in c for c in new_client_names)
        current_side = determine_party_side(p["party_type"])
        if current_side == "B": has_side_b = True
        elif current_side == "A": has_side_a = True

        if is_our_client and found_side is None and current_side in ["A", "B"]:
            found_side = current_side

    client_side = found_side if found_side else ("A" if has_side_b else ("B" if has_side_a else "A"))
    target_side = "B" if client_side == "A" else "A"

    # 3. 提取本案对手方
    new_case_opponents = set()
    for p in current_parties:
        if determine_party_side(p["party_type"]) == target_side:
            if not any(c in p["name"] or p["name"] in c for c in new_client_names):
                new_case_opponents.add(p["name"])

    valid_opponents = [opp for opp in get_valid_keywords(new_case_opponents) if len(opp) > 1]
    valid_new_clients = [c for c in get_valid_keywords(new_client_names) if len(c) > 1]

    precise_conflicts = []
    processed_keys = set()

    # 4. 在全库字典中极速扫描（替代昂贵的 LIKE '%xxx%' 查询）
    for cid, c_data in global_case_cache.items():
        if cid == case_id: continue

        # 检测 A: 起诉现有客户
        if valid_opponents:
            for p in c_data["parties"]:
                if "委托" in p["party_type"]:
                    db_name = p["name"]
                    match_level = "exact" if db_name in new_case_opponents else ("fuzzy" if any(o in db_name or db_name in o for o in valid_opponents) else None)

                    if match_level:
                        key = (cid, "agency_conflict")
                        if key not in processed_keys:
                            match_reason = f"完全匹配 '{db_name}'" if match_level == "exact" else f"匹配到关键字 '{db_name}'"
                            precise_conflicts.append({
                                "case_id": cid,
                                "case_number": c_data["case_number"],
                                "other_lawyer_name": c_data["lawyer_name"],
                                "conflict_type": "利益冲突（起诉现有客户）",
                                "match_level": match_level,
                                "role": "委托人",
                                "message": f"{'冲突匹配' if match_level == 'exact' else '疑似冲突'}：本案对手方（{match_reason}）是我所现有案件的委托人/顾问单位。"
                            })
                            processed_keys.add(key)
                        break

        # 检测 B: 现有客户作为对手
        if valid_new_clients:
            for p in c_data["parties"]:
                db_name = p["name"]
                match_level = "exact" if db_name in new_client_names else ("fuzzy" if any(c in db_name or db_name in c for c in valid_new_clients) else None)

                if match_level:
                    host_client_names = {hp["name"] for hp in c_data["parties"] if "委托" in hp["party_type"]}
                    is_returning = any(db_name in hc or hc in db_name for hc in host_client_names)
                    if is_returning: continue

                    host_side = "A"
                    if any((hc in hp["name"] or hp["name"] in hc) and determine_party_side(hp["party_type"]) == "B" for hp in c_data["parties"] for hc in host_client_names):
                        host_side = "B"

                    target_role_side = determine_party_side(p["party_type"])
                    if target_role_side != "Unknown" and host_side != target_role_side:
                        key = (cid, "self_conflict")
                        if key not in processed_keys:
                            match_reason = f"完全匹配 '{db_name}'" if match_level == "exact" else f"匹配到关键字 '{db_name}'"
                            precise_conflicts.append({
                                "case_id": cid,
                                "case_number": c_data["case_number"],
                                "other_lawyer_name": c_data["lawyer_name"],
                                "conflict_type": "利益冲突（正在起诉该客户）",
                                "match_level": match_level,
                                "role": p["party_type"],
                                "message": f"{'冲突匹配' if match_level == 'exact' else '疑似冲突'}：本案委托人（{match_reason}）在现有案件中是【{p['party_type']}】，处于对立面。"
                            })
                            processed_keys.add(key)
                        break

    if precise_conflicts:
        return {"has_conflict": True, "details": precise_conflicts}
    return {"has_conflict": False, "details": []}


@router.get("/pending", response_model=CasePageOut)
def get_pending_cases(
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=1000),
        review_status: Optional[str] = Query(None, description="按审核状态筛选：待审核/已审核/已拒绝，不传则默认待审核"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)  # 注入当前用户
):
    """
    获取审核案件列表（支持按状态筛选）
    - 不传 review_status 或传 "待审核"：返回所有待审核案件
    - 传 "已审核" 或 "已拒绝"：仅返回当前用户近7天的审核记录
    """
    # 验证审核权限
    check_review_permission(current_user)

    # 已审核/已拒绝 → 仅看当前用户近7天的记录
    reviewer_id = None
    date_from = None
    if review_status in ("已审核", "已拒绝"):
        reviewer_id = current_user.id
        date_from = datetime.now() - timedelta(days=7)

    cases = list_cases_by_status(db, skip=skip, limit=limit, review_status=review_status, reviewer_id=reviewer_id, date_from=date_from)
    total = count_cases_by_status(db, review_status=review_status, reviewer_id=reviewer_id, date_from=date_from)
    # 拦截转换：用 CaseParty 中的委托人覆盖旧的 client_name
    cases_simple = []
    for case in cases:
        simple = CaseSimpleOut.model_validate(case)
        # 动态提取类型包含“委托”的当事人名称
        clients = [p.name for p in case.parties if p.party_type and '委托' in p.party_type and p.name]
        if clients:
            simple.client_name = "、".join(clients)
        cases_simple.append(simple)
    return {"items": cases_simple, "total": total}


@router.post("/batch_review")
def batch_review_cases(
        req: BatchReviewRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    单线程真·毫秒级 批量审核API
    完全抛弃并发与ORM实例化，直接执行底层的内存对比和单次SQL批量更新
    """
    check_review_permission(current_user)
    start_time = time.time()

    success_cases = []
    conflict_cases = []
    error_cases = []

    # ========================================================
    # 步骤 1：全库轻量级扫盘，只提取基础文本数据，规避 ORM 耗时
    # ========================================================
    raw_cases = db.query(
        Case.case_id,
        Case.case_number,
        User.real_name.label("lawyer_name")
    ).outerjoin(User, Case.main_lawyer_id == User.id).filter(Case.is_deleted == False).all()

    raw_parties = db.query(
        CaseParty.case_id,
        CaseParty.party_type,
        CaseParty.name
    ).join(Case).filter(Case.is_deleted == False).all()

    # 转化为纯净的 Python 字典结构
    global_case_cache = {}
    for r in raw_cases:
        global_case_cache[r.case_id] = {
            "case_id": r.case_id,
            "case_number": r.case_number,
            "lawyer_name": r.lawyer_name or "未知",
            "parties": []
        }

    for p in raw_parties:
        if p.case_id in global_case_cache and p.name:
            global_case_cache[p.case_id]["parties"].append({
                "party_type": p.party_type or "",
                "name": p.name.strip()
            })

    # ========================================================
    # 步骤 2：在单线程内存中执行排查（无锁竞争）
    # ========================================================
    cases_to_update = []
    for case_id in req.case_ids:
        if case_id not in global_case_cache:
            error_cases.append({"case_id": case_id, "error": "案件不存在"})
            continue

        try:
            if req.review_status == "已审核" and case_id not in req.force_ids:
                # 触发纯内存比对
                conflict_result = _pure_memory_conflict_check(case_id, global_case_cache)
                if conflict_result["has_conflict"]:
                    conflict_cases.append({
                        "case_id": case_id,
                        "case_number": global_case_cache[case_id]["case_number"],
                        "conflicts": conflict_result["details"]
                    })
                    continue # 被拦截，不进入更新队列

            cases_to_update.append(case_id)
        except Exception as e:
            error_cases.append({"case_id": case_id, "error": str(e)})

    # ========================================================
    # 步骤 3：终极批量更新（合并为 1 条底层 SQL 语句！）
    # ========================================================
    if cases_to_update:
        try:
            # 构建批量更新字段
            update_fields = {
                "review_status": req.review_status,
                "reviewer_id": current_user.id,
                "reviewed_at": datetime.now()
            }
            # 如果传入了审核意见，一并更新
            if req.review_comment is not None:
                update_fields["review_comment"] = req.review_comment

            db.query(Case).filter(Case.case_id.in_(cases_to_update)).update(
                update_fields,
                synchronize_session=False  # 禁用当前会话内存同步，极大提升性能
            )
            db.commit() # 批量数据只提交 1 次！
            success_cases.extend(cases_to_update)

            # 审核驳回时，为每个案件的关联律师创建定向通知
            if req.review_status == "已拒绝":
                rejected_cases = db.query(Case).filter(Case.case_id.in_(cases_to_update)).all()
                for rc in rejected_cases:
                    create_review_rejection_notifications(db, rc, current_user.id, req.review_comment)
                db.commit()
        except Exception as e:
            db.rollback()
            for cid in cases_to_update:
                error_cases.append({"case_id": cid, "error": f"更新失败: {str(e)}"})

    # ========================================================
    # 步骤 4：统计耗时记录日志
    # ========================================================
    elapsed_ms = (time.time() - start_time) * 1000
    log_summary = (
        f"【批量审核完毕】操作人: {current_user.real_name}(ID:{current_user.id}) | "
        f"动作: {req.review_status} | "
        f"本批次总计: {len(req.case_ids)}笔 | "
        f"成功: {len(success_cases)} | 冲突拦截: {len(conflict_cases)} | 失败: {len(error_cases)} | "
        f"总耗时: {elapsed_ms:.2f} ms"
    )
    logger.info(log_summary)

    if error_cases:
        logger.warning(f"【批量审核异常明细】异常案件及原因: {error_cases}")

    return {
        "success_cases": success_cases,
        "conflict_cases": conflict_cases,
        "error_cases": error_cases
    }


@router.put("/{case_id}/review", response_model=CaseOut)
def review_case(
        case_id: int,
        review_status: str,
        review_comment: Optional[str] = Query(None, description="审核意见/修改建议"),
        force: bool = Query(False, description="是否强制通过（忽略利益冲突）"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)  # 注入当前用户
):
    """
    审核案件（通过/拒绝/撤回审核）
    - review_status="已审核": 通过（触发冲突检测）
    - review_status="已拒绝": 驳回（触发通知）
    - review_status="待审核": 撤回审核（将已审核/已拒绝回退为待审核，跳过冲突检测）
    """
    # 鉴权
    check_review_permission(current_user)

    # 1. 撤回审核逻辑（待审核）
    if review_status == "待审核":
        try:
            updated_case = update_review_status(
                db=db,
                case_id=case_id,
                review_status="待审核",
                reviewer_id=current_user.id,
                review_comment=review_comment
            )
            if not updated_case:
                raise HTTPException(status_code=404, detail="案件不存在")
            return updated_case
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # 2. 审核通过逻辑（已审核）
    if review_status == "已审核":
        # 如果不是强制通过，则进行冲突检测
        if not force:
            conflict_result = check_interest_conflict_for_case(db, case_id)
            if conflict_result["has_conflict"]:
                # 409 Conflict: 返回详细信息给前端展示
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "INTEREST_CONFLICT",
                        "message": "检测到潜在利益冲突，是否强制通过？",
                        "conflicts": conflict_result["details"]
                    }
                )

    # 3. 执行正常审核更新（已审核/已拒绝）
    try:
        updated_case = update_review_status(
            db=db,
            case_id=case_id,
            review_status=review_status,
            reviewer_id=current_user.id,  # 安全地使用 Token 解析出的用户 ID
            review_comment=review_comment  # 传入审核意见
        )
        if not updated_case:
            raise HTTPException(status_code=404, detail="案件不存在")

        return updated_case

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{case_id}/approval_form", response_class=FileResponse)
def generate_approval_form(
        case_id: int,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    生成并下载案件审批表 (Word格式)
    """
    # 1. 查询案件信息 (使用 options(joinedload(...)) 预加载 parties)
    case = db.query(Case).options(
        joinedload(Case.parties),
        joinedload(Case.main_lawyer),
        joinedload(Case.assistant_lawyer),
        joinedload(Case.assistant_lawyer_2),
        joinedload(Case.reviewer)
    ).filter(Case.case_id == case_id).first()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="案件不存在"
        )

    # 2. 校验状态
    if case.review_status != "已审核":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"当前案件状态为'{case.review_status}'，仅'已审核'案件可生成审批表"
        )

    # 3. 准备模板路径
    template_path = os.path.join(TEMPLATE_DIR, "case_approval_template.docx")
    if not os.path.exists(template_path):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器缺少审批表模板文件"
        )

    try:
        # 4. 获取填充数据
        context = get_case_approval_context(case, db)

        # 5. 渲染模板 (使用 docxtpl)
        # docxtpl 会自动匹配 Word 中的 {{client_name}} 和 context 字典中的 key
        tpl = DocxTemplate(template_path)
        tpl.render(context)

        # 6. 保存到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tpl.save(tmp.name)
            tmp_path = tmp.name

        # 7. 设置下载文件名
        filename = f"业务审批表_{case.case_number}.docx"
        from urllib.parse import quote
        encoded_filename = quote(filename)

        # 添加后台任务：响应发送后删除临时文件
        background_tasks.add_task(os.remove, tmp_path)

        return FileResponse(
            path=tmp_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )

    except Exception as e:
        print(f"Generate document error: {e}")
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成审批表失败: {str(e)}"
        )