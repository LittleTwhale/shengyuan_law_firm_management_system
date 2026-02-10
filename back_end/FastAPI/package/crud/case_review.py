# crud/case_review.py
from typing import List, Optional, cast

from sqlalchemy import or_, func
from sqlalchemy.orm import Session, joinedload

from .case import get_case_by_id, split_with_separators
from ..models.case import Case, CaseParty


def list_pending_cases(db: Session, skip: int = 0, limit: int = 100) -> List[Case]:
    """获取待审核案件列表"""
    query = db.query(Case).options(
        joinedload(Case.main_lawyer),
        joinedload(Case.assistant_lawyer),
        joinedload(Case.execution_lawyer),
        joinedload(Case.execution_assistant),
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
    db.commit()
    db.refresh(case)
    return cast(Case, case)


def count_reviewed_cases(db: Session, lawyer_id: int, year: Optional[int] = None) -> int:
    """统计审核过的案件数量"""
    query = db.query(Case).filter(Case.is_deleted == False, Case.reviewer_id == lawyer_id)
    if year:
        query = query.filter(func.extract('year', Case.commission_date) == year)
    return query.count()


def check_interest_conflict_for_case(db: Session, case_id: int):
    """
    审核时的利益冲突检测
    """
    # 1. 获取当前待审核案件及其当事人
    current_case = db.query(Case).filter(Case.case_id == case_id).first()
    if not current_case:
        return {"has_conflict": False}

    current_parties = current_case.parties  # 利用 relationship 加载

    # 定义阵营集合
    side_a = {'原告', '申请人', '上诉人'}
    side_b = {'被告', '被申请人', '被上诉人'}

    # ---------------------------------------------------------
    # 2. 提取当前案件的委托人 (New Clients)
    # ---------------------------------------------------------
    new_client_names = set()
    for p in current_parties:
        if p.party_type == '委托人' and p.name:
            new_client_names.add(p.name.strip())

    # 兜底：如果 Party 表没数据，尝试用 client_name
    if not new_client_names and current_case.client_name:
        new_client_names.add(current_case.client_name.strip())

    if not new_client_names:
        return {"has_conflict": False, "details": []}

    # ---------------------------------------------------------
    # 3. 确定委托人阵营 & 锁定对手 (Opponents)
    # ---------------------------------------------------------
    client_side = "A"  # 默认为原告方

    # 3.1 判断当前委托人是在哪个阵营 (或者推断阵营)
    found_side = None
    has_side_b_party = False

    for p in current_parties:
        if p.name.strip() in new_client_names:
            if p.party_type in side_b:
                found_side = "B"
            elif p.party_type in side_a:
                found_side = "A"
        if p.party_type in side_b:
            has_side_b_party = True

    if found_side:
        client_side = found_side
    else:
        # 如果委托人没挂头衔，且案件里有被告，那委托人通常是原告
        if has_side_b_party:
            client_side = "A"
        else:
            # 只有原告没有被告，委托人可能是被告（较少见）
            has_side_a = any(p.party_type in side_a for p in current_parties)
            if has_side_a:
                client_side = "B"

    # 3.2 提取本案对手名字
    target_opponent_types = side_a if client_side == "B" else side_b
    new_case_opponents = set()

    for p in current_parties:
        if p.party_type in target_opponent_types and p.name:
            new_case_opponents.add(p.name.strip())

    # ---------------------------------------------------------
    # 4. 执行双向检测
    # ---------------------------------------------------------
    precise_conflicts = []
    processed_keys = set()  # (case_id, conflict_type) 去重

    # === 检测 A: 代理冲突 (起诉现有客户) ===
    # 逻辑：本案的对手，是不是我们其他未结案件的委托人？
    if new_case_opponents:
        existing_client_conflicts = db.query(CaseParty).join(Case).filter(
            CaseParty.party_type == '委托人',
            CaseParty.name.in_(new_case_opponents),
            Case.is_deleted == False,
            Case.case_id != case_id  # 排除自己
        ).all()

        for record in existing_client_conflicts:
            c = record.case
            key = (c.case_id, "agency_conflict")
            if key in processed_keys: continue

            msg = f"本案对手方 '{record.name}' 是我所现有案件的委托人。"
            if c.case_category == "法律顾问业务":
                msg = f"本案对手方 '{record.name}' 是我所法律顾问单位。"

            precise_conflicts.append({
                "case_id": c.case_id,  # 关键：返回ID供前端跳转
                "case_number": c.case_number,
                "other_lawyer_name": c.main_lawyer.real_name if c.main_lawyer else "未知",
                "conflict_type": "利益冲突（起诉现有客户）",
                "role": "委托人",
                "message": msg
            })
            processed_keys.add(key)

    # === 检测 B: 自益冲突 (正在起诉该客户) ===
    # 逻辑：本案的委托人，在我们其他案件中是不是处于对手方？
    history_participations = db.query(CaseParty).join(Case).filter(
        CaseParty.name.in_(new_client_names),
        Case.is_deleted == False,
        Case.case_id != case_id
    ).all()

    for party_record in history_participations:
        c = party_record.case

        # 1. 查该历史案件的委托人
        host_clients = db.query(CaseParty).filter(
            CaseParty.case_id == c.case_id,
            CaseParty.party_type == '委托人'
        ).all()
        host_client_names = {hc.name for hc in host_clients}

        # 如果是回头客（两边都是委托人），不算冲突
        if party_record.name in host_client_names:
            continue

        # 2. 判断阵营对立
        # 历史案件委托人是 A 还是 B？
        host_side = "A"  # 默认原告
        all_c_parties = c.parties

        has_host_as_defendant = any(
            p.name in host_client_names and p.party_type in side_b
            for p in all_c_parties
        )
        if has_host_as_defendant:
            host_side = "B"

        # 本案委托人在历史案件中是 A 还是 B？
        target_role_side = "Unknown"
        if party_record.party_type in side_a:
            target_role_side = "A"
        elif party_record.party_type in side_b:
            target_role_side = "B"

        # 3. 如果阵营不同，则是冲突
        if target_role_side != "Unknown" and host_side != target_role_side:
            key = (c.case_id, "self_conflict")
            if key in processed_keys: continue

            precise_conflicts.append({
                "case_id": c.case_id,
                "case_number": c.case_number,
                "other_lawyer_name": c.main_lawyer.real_name if c.main_lawyer else "未知",
                "conflict_type": "利益冲突（正在起诉该客户）",
                "role": party_record.party_type,
                "message": f"本案委托人 '{party_record.name}' 在现有案件中是【{party_record.party_type}】，处于对立面。"
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