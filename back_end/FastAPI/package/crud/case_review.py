# crud/case_review.py
from typing import List, Optional, cast
from sqlalchemy.orm import Session, joinedload
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


def update_review_status(db: Session, case_id: int, review_status: str) -> Optional[Case]:
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
    db.commit()
    db.refresh(case)
    return cast(Case, case)