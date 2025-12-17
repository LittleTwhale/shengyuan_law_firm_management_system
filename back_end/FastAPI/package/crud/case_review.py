# crud/case_review.py
from typing import List, Optional, cast

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from .case import get_case_by_id, split_with_separators
from ..models.case import Case


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


def count_reviewed_cases(db: Session, lawyer_id: int) -> int:
    """统计审核过的案件数量"""
    return db.query(Case).filter(Case.is_deleted == False, Case.reviewer_id == lawyer_id).count()


def check_interest_conflict_for_case(db: Session, case_id: int):
    """
    根据案件ID检查利益冲突
    """
    # 获取当前案件信息
    case = get_case_by_id(db, case_id)
    if not case:
        return {"has_conflict": False}

    client_name = case.client_name
    if not client_name:
        return {"has_conflict": False}

    # 1. 获取所有顾问单位（法律顾问业务的委托人）
    consultant_units = db.query(Case.client_name).filter(
        Case.case_category == "法律顾问业务",
        Case.is_deleted == False,
        Case.case_id != case_id  # 排除当前案件
    ).distinct().all()
    consultant_units = [unit[0] for unit in consultant_units]  # 提取委托人名称列表

    # 定义分隔符
    separators = ["、", ",", "，", " ", "；", ";"]

    # 拆分当前案件的被告
    current_defendants = [d.strip() for d in split_with_separators(case.defendant or "", separators) if d.strip()]

    precise_conflicts = []

    # 2. 检测1：常规利益冲突 - 当前委托人在其他案件中作为原告/被告
    conflict_cases = db.query(Case).filter(
        or_(
            Case.plaintiff.like(f"%{client_name}%"),
            Case.defendant.like(f"%{client_name}%")
        ),
        Case.is_deleted == False,
        Case.case_id != case_id  # 排除当前案件
    ).all()

    for conflict_case in conflict_cases:
        # 拆分原告/被告为列表
        plaintiffs = [p.strip() for p in split_with_separators(str(conflict_case.plaintiff), separators) if p.strip()]
        defendants = [d.strip() for d in split_with_separators(conflict_case.defendant or "", separators) if d.strip()]

        # 常规冲突判断
        normal_conflict = client_name in plaintiffs or client_name in defendants

        if normal_conflict:
            conflict_info = {
                "case": conflict_case,
                "conflict_type": "常规利益冲突",
                "role": "原告" if client_name in plaintiffs else "被告",
                "conflict_reason": f"当前委托人在案件 {conflict_case.case_number} 中作为{('原告' if client_name in plaintiffs else '被告')}"
            }
            precise_conflicts.append(conflict_info)

    # 3. 检测2：顾问单位冲突 - 当前案件的被告包含顾问单位
    # 这部分独立执行，不依赖于conflict_cases
    consultant_conflict_units = []
    for unit in consultant_units:
        if unit in current_defendants:
            consultant_conflict_units.append(unit)

    if consultant_conflict_units:
        # 为每个冲突的顾问单位创建一个冲突记录
        for unit in consultant_conflict_units:
            # 查找该顾问单位对应的法律顾问业务案件
            consultant_case = db.query(Case).filter(
                Case.client_name == unit,
                Case.case_category == "法律顾问业务",
                Case.is_deleted == False
            ).first()

            if consultant_case:
                conflict_info = {
                    "case": consultant_case,  # 使用法律顾问业务案件信息
                    "conflict_type": "顾问单位作为被告",
                    "role": "被告（顾问单位）",
                    "conflict_reason": f"当前案件的被告 '{unit}' 是本所法律顾问单位",
                    "consultant_unit": unit
                }
                precise_conflicts.append(conflict_info)

    if precise_conflicts:
        # 提取冲突详情
        conflict_details = []
        for item in precise_conflicts:
            conflict_case = item["case"]
            detail = {
                "case_id": conflict_case.case_id,
                "case_number": conflict_case.case_number,
                "other_lawyer_id": conflict_case.main_lawyer_id,
                "other_lawyer_name": conflict_case.main_lawyer.real_name if conflict_case.main_lawyer else "未知",
                "role": item["role"],
                "conflict_case_category": conflict_case.case_category,
                "conflict_type": item["conflict_type"],
                "message": item["conflict_reason"]
            }
            if "consultant_unit" in item:
                detail["consultant_unit"] = item["consultant_unit"]

            conflict_details.append(detail)

        return {"has_conflict": True, "details": conflict_details}

    return {"has_conflict": False}


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