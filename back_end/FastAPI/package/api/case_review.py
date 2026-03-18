# api/case_review.py
import os
import tempfile

from docxtpl import DocxTemplate
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi import BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from .deps import get_current_active_user
from ..core.config import TEMPLATE_DIR
from ..crud.case_review import list_pending_cases, count_pending_cases, update_review_status, \
    check_interest_conflict_for_case, get_case_approval_context
from ..database.database import get_db
from ..models.case import Case
from ..models.user import User
from ..schemas.case import CasePageOut, CaseSimpleOut, CaseOut

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


@router.get("/pending", response_model=CasePageOut)
def get_pending_cases(
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)  # 注入当前用户
):
    """
    获取待审核案件列表
    """
    # 验证审核权限
    check_review_permission(current_user)

    cases = list_pending_cases(db, skip=skip, limit=limit)
    total = count_pending_cases(db)
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


@router.put("/{case_id}/review", response_model=CaseOut)
def review_case(
        case_id: int,
        review_status: str,
        force: bool = Query(False, description="是否强制通过（忽略利益冲突）"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)  # 注入当前用户
):
    """
    审核案件（通过/拒绝）
    """
    # 鉴权
    check_review_permission(current_user)

    # 1. 审核通过逻辑
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

    # 2. 执行更新
    try:
        updated_case = update_review_status(
            db=db,
            case_id=case_id,
            review_status=review_status,
            reviewer_id=current_user.id  # 安全地使用 Token 解析出的用户 ID
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
        context = get_case_approval_context(case,db)

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