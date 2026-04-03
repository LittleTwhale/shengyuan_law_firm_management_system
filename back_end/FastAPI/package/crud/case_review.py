# crud/case_review.py
from datetime import datetime
from typing import List, Optional, cast, Dict, Any

from sqlalchemy import or_, func
from sqlalchemy.orm import Session, joinedload, selectinload

from ..models.case import Case, CaseParty
from ..utils.keywords_helper import determine_party_side, get_valid_keywords


def list_pending_cases(db: Session, skip: int = 0, limit: int = 100) -> List[Case]:
    """获取待审核案件列表"""
    query = db.query(Case).options(
        joinedload(Case.main_lawyer),
        joinedload(Case.assistant_lawyer),
        joinedload(Case.assistant_lawyer_2),
        joinedload(Case.execution_lawyer),
        joinedload(Case.execution_assistant),
        joinedload(Case.parties),
    ).filter(
        Case.review_status == "待审核",  # 只筛选待审核案件
        Case.is_deleted == False
    )

    return cast(List[Case], query.offset(skip).limit(limit).all())


def count_pending_cases(db: Session) -> int:
    """统计待审核案件总数"""
    query = db.query(Case).filter(
        Case.review_status == "待审核",
        Case.is_deleted == False
    )

    return query.count()


def update_review_status(db: Session, case_id: int, review_status: str, reviewer_id: int) -> Optional[Case]:
    """更新案件审核状态（已审核/已拒绝）"""
    case = db.query(Case).filter(
        Case.case_id == case_id,
        Case.is_deleted == False
    ).first()

    if not case:
        return None

    # 验证状态值合法性
    if review_status not in ["已审核", "已拒绝"]:
        raise ValueError("审核状态必须是'已审核'或'已拒绝'")

    case.review_status = review_status
    case.reviewer_id = reviewer_id  # 记录审核人ID
    case.reviewed_at = datetime.now()  # 记录审核时间
    db.commit()
    db.refresh(case)
    return cast(Case, case)


def count_reviewed_cases(db: Session, lawyer_id: int, year: Optional[int] = None) -> int:
    """统计审核过的案件数量"""
    query = db.query(Case).filter(Case.is_deleted == False, Case.reviewer_id == lawyer_id)
    if year:
        query = query.filter(func.extract('year', Case.reviewed_at) == year)
    return query.count()


def check_interest_conflict_for_case(db: Session, case_id: int):
    """
    单条审核时的利益冲突检测 (两步法 + selectinload 极致优化版)
    """
    current_case = db.query(Case).options(
        selectinload(Case.parties),
        selectinload(Case.bank_case_details)
    ).filter(Case.case_id == case_id).first()

    if not current_case:
        return {"has_conflict": False}

    # ====== 提取待审案件的支行名称  ======
    branch_name = None
    if current_case.case_category == "银行案件" and current_case.bank_case_details and current_case.bank_case_details.branch_name:
        branch_name = current_case.bank_case_details.branch_name.strip()
    # ====================================================

    current_parties = current_case.parties

    new_client_names = set()
    for p in current_parties:
        if p.party_type and "委托" in p.party_type and p.name:
            new_client_names.add(p.name.strip())

    if not new_client_names and current_case.client_name:
        new_client_names.add(current_case.client_name.strip())

    if not new_client_names:
        return {"has_conflict": False, "details": []}

    client_side = "A"
    found_side = None
    has_side_b = False
    has_side_a = False

    for p in current_parties:
        p_name = p.name.strip() if p.name else ""
        if not p_name: continue

        is_our_client = any(
            (client_name in p_name or p_name in client_name)
            for client_name in new_client_names
        )

        current_side = determine_party_side(p.party_type)
        if current_side == "B":
            has_side_b = True
        elif current_side == "A":
            has_side_a = True

        if is_our_client and found_side is None:
            if current_side in ["A", "B"]:
                found_side = current_side

    if found_side:
        client_side = found_side
    else:
        if has_side_b:
            client_side = "A"
        elif has_side_a:
            client_side = "B"
        else:
            client_side = "A"

    target_side_to_find = "B" if client_side == "A" else "A"
    new_case_opponents = set()

    for p in current_parties:
        p_name = p.name.strip() if p.name else ""
        if not p_name: continue

        if determine_party_side(p.party_type) == target_side_to_find:
            is_self = any((client_name in p_name or p_name in client_name) for client_name in new_client_names)
            if not is_self:
                new_case_opponents.add(p_name)

    precise_conflicts = []
    processed_keys = set()

    # 防止提取出单字（如“王”），引发毁灭性全表扫描
    valid_opponents = [opp for opp in get_valid_keywords(new_case_opponents) if len(opp) > 1]

    # === 检测 A: 代理冲突 ===
    if valid_opponents:
        like_conditions = [CaseParty.name.like(f"%{opp}%") for opp in valid_opponents]

        # 优化点：第一步仅获取极轻量的整数 case_id
        matched_case_ids_query = db.query(CaseParty.case_id).join(Case).filter(
            CaseParty.party_type.like('%委托%'),
            or_(*like_conditions),
            Case.is_deleted == False,
            Case.case_id != case_id
        ).distinct().all()
        matched_case_ids = [r[0] for r in matched_case_ids_query]

        if matched_case_ids:
            # 优化点：第二步用 selectinload 精准拉取对象
            existing_cases = db.query(Case).options(
                selectinload(Case.parties),
                selectinload(Case.bank_case_details),
                joinedload(Case.main_lawyer)
            ).filter(Case.case_id.in_(matched_case_ids)).all()

            for c in existing_cases:
                match_level = None
                matched_db_name = ""
                for p in c.parties:
                    if p.party_type and '委托' in p.party_type:
                        db_name = p.name.strip() if p.name else ""
                        if db_name in new_case_opponents:
                            match_level = "exact"
                            matched_db_name = db_name
                            break
                        else:
                            for opp in valid_opponents:
                                if opp in db_name or db_name in opp:
                                    # ====== 银行案件支行双重校验 ======
                                    is_bank_case_db = c.case_category == "银行案件"
                                    is_generic_bank_name = any(gb in opp for gb in ["银行", "农商行", "信用社"])

                                    if is_generic_bank_name:
                                        if branch_name and branch_name not in db_name:
                                            continue
                                        if is_bank_case_db and c.bank_case_details and c.bank_case_details.branch_name:
                                            db_branch = c.bank_case_details.branch_name.strip()
                                            if db_branch not in opp:
                                                continue
                                    # ==============================================
                                    match_level = "fuzzy"
                                    matched_db_name = db_name
                                    break
                    if match_level:
                        break

                if not match_level:
                    continue

                key = (c.case_id, "agency_conflict")
                if key in processed_keys: continue

                prefix_text = "冲突匹配" if match_level == "exact" else "疑似冲突"
                match_reason = f"完全匹配 '{matched_db_name}'" if match_level == "exact" else f"匹配到关键字 '{matched_db_name}'"

                precise_conflicts.append({
                    "case_id": c.case_id,
                    "case_number": c.case_number,
                    "other_lawyer_name": c.main_lawyer.real_name if c.main_lawyer else "未知",
                    "conflict_type": "利益冲突（起诉现有客户）",
                    "match_level": match_level,
                    "role": "委托人",
                    "message": f"{prefix_text}：本案对手方（{match_reason}）是我所现有案件的委托人/顾问单位。"
                })
                processed_keys.add(key)

    # === 检测 B: 自益冲突 ===
    valid_new_clients = [c for c in get_valid_keywords(new_client_names) if len(c) > 1]

    if valid_new_clients:
        client_like_conditions = [CaseParty.name.like(f"%{client}%") for client in valid_new_clients]

        # 第一步：只查ID
        history_case_ids_query = db.query(CaseParty.case_id).join(Case).filter(
            or_(*client_like_conditions),
            Case.is_deleted == False,
            Case.case_id != case_id
        ).distinct().all()
        history_case_ids = [r[0] for r in history_case_ids_query]

        if history_case_ids:
            # 第二步：使用 selectinload 拉取
            history_cases = db.query(Case).options(
                selectinload(Case.parties),
                selectinload(Case.bank_case_details),
                joinedload(Case.main_lawyer)
            ).filter(Case.case_id.in_(history_case_ids)).all()

            for c in history_cases:
                matched_party = None
                match_level = None
                matched_db_name = ""

                for p in c.parties:
                    db_name = p.name.strip() if p.name else ""
                    if not db_name: continue

                    if db_name in new_client_names:
                        match_level = "exact"
                        matched_party = p
                        matched_db_name = db_name
                        break
                    else:
                        for c_kw in valid_new_clients:
                            if c_kw in db_name or db_name in c_kw:
                                # ====== 银行案件支行双重校验 ======
                                is_bank_case_db = c.case_category == "银行案件"
                                is_generic_bank_name = any(gb in c_kw for gb in ["银行", "农商行", "信用社"])

                                if is_generic_bank_name:
                                    if branch_name and branch_name not in db_name:
                                        continue
                                    if is_bank_case_db and c.bank_case_details and c.bank_case_details.branch_name:
                                        db_branch = c.bank_case_details.branch_name.strip()
                                        if db_branch not in c_kw:
                                            continue
                                # ==============================================
                                match_level = "fuzzy"
                                matched_party = p
                                matched_db_name = db_name
                                break
                    if match_level:
                        break

                if not match_level or not matched_party:
                    continue

                host_clients = [p for p in c.parties if p.party_type and '委托' in p.party_type]
                host_client_names = {hc.name.strip() for hc in host_clients if hc.name}

                is_returning_client = any(
                    matched_db_name in hc_name or hc_name in matched_db_name
                    for hc_name in host_client_names
                )
                if is_returning_client: continue

                host_side = "A"
                has_host_as_defendant = any(
                    (hc_name in p.name or p.name in hc_name) and determine_party_side(p.party_type) == "B"
                    for p in c.parties for hc_name in host_client_names
                )
                if has_host_as_defendant: host_side = "B"

                target_role_side = determine_party_side(matched_party.party_type)

                if target_role_side != "Unknown" and host_side != target_role_side:
                    key = (c.case_id, "self_conflict")
                    if key in processed_keys: continue

                    prefix_text = "冲突匹配" if match_level == "exact" else "疑似冲突"
                    match_reason = f"完全匹配 '{matched_db_name}'" if match_level == "exact" else f"匹配到关键字 '{matched_db_name}'"

                    precise_conflicts.append({
                        "case_id": c.case_id,
                        "case_number": c.case_number,
                        "other_lawyer_name": c.main_lawyer.real_name if c.main_lawyer else "未知",
                        "conflict_type": "利益冲突（正在起诉该客户）",
                        "match_level": match_level,
                        "role": matched_party.party_type,
                        "message": f"{prefix_text}：本案委托人（{match_reason}）在现有案件中是【{matched_party.party_type}】，处于对立面。"
                    })
                    processed_keys.add(key)

    if precise_conflicts:
        return {"has_conflict": True, "details": precise_conflicts}

    return {"has_conflict": False, "details": []}


def replace_text_in_paragraph(paragraph, context):
    """
    辅助函数：替换段落中的占位符
    注意：python-docx 的 runs 可能会把 {{key}} 切割开，这里使用简单的全文本替换。
    如果格式保留要求极高，可能需要更复杂的 run 遍历逻辑。
    """
    if not paragraph.text:
        return

    # 简单检查是否有任何占位符在段落文本中
    has_placeholder = False
    for key in context.keys():
        if key in paragraph.text:
            has_placeholder = True
            break

    if not has_placeholder:
        return

    # 简单替换策略：直接替换 paragraph.text 会丢失部分样式(font等)
    # 但对于表格填空通常是可以接受的。
    # 稍微好一点的方法是保留第一个 run 的样式，清空后面的。

    # 这里使用最简单有效的方法：遍历 key 进行 replace
    # 注意：这可能会重置该段落的样式为默认样式。
    # 如果要保留样式，通常建议使用 python-docx-template 库，
    # 但为了不引入新依赖，我们使用原生替换。

    current_text = paragraph.text
    for key, value in context.items():
        if key in current_text:
            current_text = current_text.replace(key, value)

    # 如果文本发生了变化，更新段落
    if current_text != paragraph.text:
        paragraph.text = current_text


def get_case_approval_context(case: Case, db: Session) -> Dict[str, Any]:
    """
    将 Case 对象转换为案件审批表模版所需的上下文 context
    适配 CaseParty 数据结构
    """

    # 1. 初始化容器
    clients = []  # 委托人列表
    client_phones = []  # 委托人电话
    client_ids = []  # 委托人证件号

    plaintiffs = []  # 原告/申请人
    defendants = []  # 被告/被告人/被申请人
    appellants = []  # 上诉人
    appellees = []  # 被上诉人

    # 定义归类映射 (根据您实际存入数据库的 party_type 字符串进行调整)
    # 假设数据库中存储的是 '原告', '申请人', '被告', '委托人' 等标准术语
    type_map = {
        'client': ['委托人'],
        'plaintiff': ['原告', '申请人', ],
        'defendant': ['被告', '被告人', '被申请人', ],
        'appellant': ['上诉人'],
        'appellee': ['被上诉人']
    }

    # 2. 遍历关联的当事人列表
    # 确保 case.parties 已经被加载 (SQLAlchemy lazy load)
    if case.parties:
        for party in case.parties:
            ptype = party.party_type.strip() if party.party_type else ""
            name = party.name.strip() if party.name else ""

            if not name:
                continue

            # --- 归类逻辑 ---
            if ptype in type_map['client']:
                clients.append(name)
                if party.phone:
                    client_phones.append(party.phone)
                if party.id_number:
                    client_ids.append(party.id_number)

            elif ptype in type_map['plaintiff']:
                plaintiffs.append(name)

            elif ptype in type_map['defendant']:
                defendants.append(name)

            elif ptype in type_map['appellant']:
                appellants.append(name)

            elif ptype in type_map['appellee']:
                appellees.append(name)

    # 3. 拼接字符串 (处理多人情况)
    # 使用顿号或逗号分隔
    def join_str(str_list):
        return "、".join(str_list) if str_list else ""

    # 4.判断是否重大案件
    is_major_str = "是" if case.is_major else "否"

    # 5. 调用已有的利益冲突检测函数
    conflict_result = check_interest_conflict_for_case(db, case.case_id)
    if conflict_result.get("has_conflict"):
        # 如果存在冲突，可以简述，或者提示去系统查看详情
        conflict_status = "存在疑似利益冲突 (请核对系统详情)"
    else:
        conflict_status = "未发现利益冲突"

    # 6. 构建模版上下文 (Key 必须与 docx 模版中的 {{key}} 对应)
    # === 合并助理律师姓名逻辑 ===
    assistants = []
    if case.assistant_lawyer:
        assistants.append(case.assistant_lawyer.real_name)
    if case.assistant_lawyer_2:
        assistants.append(case.assistant_lawyer_2.real_name)
    assistant_names_str = "、".join(assistants)

    context = {
        # --- 替换旧字段逻辑 ---
        "client_name": join_str(clients),
        "client_phone": " ".join(client_phones),  # 电话通常用空格分隔更易读
        "client_id_number": " ".join(client_ids),

        "plaintiff": join_str(plaintiffs),
        "defendant": join_str(defendants),

        "appellant_info": join_str(appellants),  # 对应模版 {{appellant_info}}
        "extra_appellant_info": join_str(appellees),  # 对应模版 {{extra_appellant_info}}

        # --- 保持原有基础字段不变 ---
        "case_number": case.case_number,
        "commission_date": case.commission_date.strftime("%Y-%m-%d") if case.commission_date else "",
        "court": case.court or "",
        "case_category": case.case_category or "",
        "cause": case.cause or "",
        "main_lawyer_name": case.main_lawyer.real_name if case.main_lawyer else "",
        "assistant_lawyer_name": assistant_names_str,
        "fee_method": case.fee_method or "",
        "case_income": str(case.case_income or 0),
        "is_major": is_major_str,
        "conflict_status": conflict_status,
        "details": case.details or "无",

        # 审核相关
        "review_status": case.review_status or "",
        "reviewer_name": case.reviewer.real_name if case.reviewer else "",

        # 导出时间
        "export_time": datetime.now().strftime("%Y-%m-%d"),
    }

    # 兜底：如果 CaseParty 没数据（旧数据），回退使用 Case 表字段
    if not clients and case.client_name:
        context["client_name"] = case.client_name
        context["client_phone"] = case.client_phone
        context["client_id_number"] = case.client_id_number

    if not plaintiffs and case.plaintiff:
        context["plaintiff"] = case.plaintiff

    if not defendants and case.defendant:
        context["defendant"] = case.defendant

    return context