# api/case_review.py
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..crud.case_operation import (
    list_pending_operations,
    get_operation_by_id,
    review_operation,
    list_user_operations,
    list_all_operations,
    get_user_name
)
from ..database.database import get_db
from ..schemas.case_operation import CaseOperationOut, CaseOperationUpdate
from ..models.case_operation import CaseOperation  # ORM模型

router = APIRouter(
    prefix="/case_review",
    tags=["case_review"]
)


def parse_pending_data(op: CaseOperation, db: Session) -> CaseOperationOut:
    """
    将 ORM 对象转换为 Pydantic 模型，并解析 pending_data 生成 details 列表
    同时填充 user_name 和 review_user_name
    """
    # 基础转换
    op_out = CaseOperationOut.model_validate(op)

    # 填充操作用户姓名
    op_out.user_name = get_user_name(db, op.user_id)
    # 填充审核用户姓名
    op_out.review_user_name = get_user_name(db, op.review_user_id)

    # 解析 pending_data
    details: List[Dict[str, Any]] = []
    pd: Dict[str, Any] = op.pending_data or {}

    if op.operation_type == "新增":
        for key, value in pd.items():
            details.append({"field": key, "old_value": None, "new_value": value})
    elif op.operation_type == "修改":
        for key, change in pd.items():
            old_val = change.get("old") if isinstance(change, dict) else None
            new_val = change.get("new") if isinstance(change, dict) else change
            details.append({"field": key, "old_value": old_val, "new_value": new_val})
    elif op.operation_type == "删除":
        for key, value in pd.items():
            details.append({"field": key, "old_value": value, "new_value": None})

    op_out.details = details
    return op_out


# -------------------------
# 1 查看所有待审核操作（管理员/所有者用）
# -------------------------
@router.get("/pending", response_model=List[CaseOperationOut])
def get_pending_operations(role: str, db: Session = Depends(get_db)):
    if role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="无权限查看待审核案件")

    ops_orm = list_pending_operations(db)
    return [parse_pending_data(op, db) for op in ops_orm]


# -------------------------
# 2 查看指定操作记录
# -------------------------
@router.get("/{operation_id}", response_model=CaseOperationOut)
def get_operation(operation_id: int, role: str, db: Session = Depends(get_db)):
    op_orm = get_operation_by_id(db, operation_id)
    if not op_orm:
        raise HTTPException(status_code=404, detail="操作记录不存在")

    if role == "user":
        raise HTTPException(status_code=403, detail="无权限查看他人操作记录")

    return parse_pending_data(op_orm, db)


# -------------------------
# 3 审核操作（通过或拒绝）
# -------------------------
@router.put("/{operation_id}/review", response_model=CaseOperationOut)
def review_case_operation(
    operation_id: int,
    review_data: CaseOperationUpdate,
    role: str,
    review_user_id: int,
    db: Session = Depends(get_db)
):
    if role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="无权限审核案件")

    if not review_data.review_status or review_data.review_status not in ["已通过", "已拒绝"]:
        raise HTTPException(status_code=400, detail="审核状态必须为 '已通过' 或 '已拒绝'")

    approved = review_data.review_status == "已通过"
    review_remark = review_data.review_remark

    # 审核记录本身
    op_orm = review_operation(
        db=db,
        operation_id=operation_id,
        review_user_id=review_user_id,
        approved=approved,
        review_remark=review_remark
    )

    if not op_orm:
        raise HTTPException(status_code=404, detail="操作记录不存在或已审核")

    # 如果审核通过，则根据操作类型更新 case 表
    if approved:
        from ..crud.case import create_case, update_case, delete_case

        if op_orm.operation_type == "新增":
            create_case(db, op_orm.pending_data)
        elif op_orm.operation_type == "修改":
            if not op_orm.case_id:
                raise HTTPException(status_code=400, detail="修改操作缺少 case_id")
            update_case(db, op_orm.case_id, op_orm.pending_data)
        elif op_orm.operation_type == "删除":
            if not op_orm.case_id:
                raise HTTPException(status_code=400, detail="删除操作缺少 case_id")
            delete_case(db, op_orm.case_id)

    # 返回解析后的操作记录
    return parse_pending_data(op_orm, db)


# -------------------------
# 4 查看用户提交的历史操作记录
# -------------------------
@router.get("/history/{user_id}", response_model=List[CaseOperationOut])
def get_user_history(user_id: int, role: str, db: Session = Depends(get_db)):
    if role == "user":
        raise HTTPException(status_code=403, detail="无权限查看他人操作记录")

    ops_orm = list_user_operations(db, user_id)
    return [parse_pending_data(op, db) for op in ops_orm]


# -------------------------
# 5️ 查看所有历史操作记录（管理员用）
# -------------------------
@router.get("/all", response_model=List[CaseOperationOut])
def get_all_operations(role: str, db: Session = Depends(get_db)):
    if role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="无权限查看操作记录")

    ops_orm = list_all_operations(db)
    return [parse_pending_data(op, db) for op in ops_orm]
