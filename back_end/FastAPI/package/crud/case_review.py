# crud/case_review.py
from typing import List, Optional, cast
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

    # 查询冲突案件：其他律师的案件中，委托人是原告或被告
    conflict_cases = db.query(Case).filter(
        # 核心：使用like匹配包含关系，兼容多主体分隔
        (Case.plaintiff.like(f"%{client_name}%")) |  # 原告中包含委托人
        (Case.defendant.like(f"%{client_name}%")),  # 被告中包含委托人
        # 排除已删除的案件和当前案件
        Case.is_deleted == False,
        Case.case_id != case_id
    ).all()

    # 进一步精确过滤
    separators = ["、", ",", "，", " ", "；", ";"]
    precise_conflicts = []
    for conflict_case in conflict_cases:
        # 拆分原告字段为主体列表
        plaintiffs = [p.strip() for p in split_with_separators(str(conflict_case.plaintiff), separators) if p.strip()]
        # 拆分被告字段为主体列表
        defendants = [d.strip() for d in split_with_separators(conflict_case.defendant or "", separators) if d.strip()]

        # 检查委托人是否在原告或被告列表中
        if client_name in plaintiffs or client_name in defendants:
            precise_conflicts.append(conflict_case)

    if precise_conflicts:
        # 提取冲突详情
        conflict_details = []
        for conflict_case in precise_conflicts:
            # 重新计算当前冲突案件的原告/被告列表
            plaintiffs = [p.strip() for p in split_with_separators(str(conflict_case.plaintiff), separators) if
                          p.strip()]
            defendants = [d.strip() for d in split_with_separators(conflict_case.defendant or "", separators) if
                          d.strip()]

            role = "原告" if client_name in plaintiffs else "被告"
            conflict_details.append({
                "case_id": conflict_case.case_id,
                "case_number": conflict_case.case_number,
                "other_lawyer_id": conflict_case.main_lawyer_id,
                "other_lawyer_name": conflict_case.main_lawyer.real_name if conflict_case.main_lawyer else "未知",
                "role": role,
                "conflict_case_category": conflict_case.case_category
            })

        return {"has_conflict": True, "details": conflict_details}

    return {"has_conflict": False}