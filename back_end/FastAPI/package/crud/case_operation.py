# crud/case_operation.py
from datetime import timezone, datetime

from sqlalchemy.orm import Session

from typing import List, Optional,cast

from ..models.case_operation import CaseOperation
from ..models.user import User  # 用于获取姓名


# 获取所有待审核的操作记录
def list_pending_operations(db: Session) -> List[CaseOperation]:
    return cast(List[CaseOperation],db.query(CaseOperation).filter(
        CaseOperation.review_status == "待审核"
    ).all())


# 根据操作ID获取操作记录
def get_operation_by_id(db: Session, operation_id: int) -> Optional[CaseOperation]:
    return db.query(CaseOperation).filter(
        CaseOperation.operation_id == operation_id
    ).first()


# 审核操作
def review_operation(
    db: Session,
    operation_id: int,
    review_user_id: int,
    approved: bool,
    review_remark: Optional[str] = None
) -> Optional[CaseOperation]:
    op = get_operation_by_id(db, operation_id)
    if not op or op.review_status != "待审核":
        return None

    op.review_status = "已通过" if approved else "已拒绝"
    op.review_user_id = review_user_id
    op.review_remark = review_remark

    from datetime import datetime
    op.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(op)
    return op


# 获取某个用户的历史操作记录
def list_user_operations(db: Session, user_id: int) -> List[CaseOperation]:
    return cast(List[CaseOperation],db.query(CaseOperation).filter(
        CaseOperation.user_id == user_id
    ).all())


# 获取所有操作记录
def list_all_operations(db: Session) -> List[CaseOperation]:
    return cast(List[CaseOperation],db.query(CaseOperation).all())


# 辅助函数：根据 user_id 获取 user_name
def get_user_name(db: Session, user_id: Optional[int]) -> Optional[str]:
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    return user.real_name if user else None

# 创建案件操作
def create_case_operation(
    db: Session,
    user_id: int,
    operation_type: str,
    pending_data: dict,
    case_id: Optional[int] = None
) -> CaseOperation:
    op = CaseOperation(
        user_id=user_id,
        operation_type=operation_type,
        pending_data=pending_data,
        case_id=case_id,
        review_status="待审核",  # 默认状态
        created_at=datetime.now(timezone.utc),
    )
    db.add(op)
    db.commit()
    db.refresh(op)
    return op