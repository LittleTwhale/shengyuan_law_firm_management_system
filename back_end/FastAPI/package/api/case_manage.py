# api/case_manage.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database.database import get_db
from ..schemas.user import UserOut
from ..schemas.case import CaseOut,CasePageOut
from ..schemas.case_operation import CaseOperationCreate, CaseOperationOut
from ..crud.user import get_all_lawyers
from ..crud.case import list_cases_by_user_role, get_case_by_id, count_cases_by_user_role
from ..crud.case_operation import create_case_operation, list_user_operations, get_operation_by_id

router = APIRouter(
    prefix="/cases",
    tags=["case_manage"]
)


# 1️⃣ 获取正式生效案件列表（分页可选）
@router.get("/", response_model=CasePageOut)
def get_cases(user_id: int, role: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    获取案件列表
    """
    cases = list_cases_by_user_role(db=db, user_id=user_id, role=role, skip=skip, limit=limit)
    total = count_cases_by_user_role(db=db, user_id=user_id, role=role)
    return {"items": cases, "total": total}


# 2️⃣ 获取单条案件详情
@router.get("/{case_id}", response_model=CaseOut)
def get_case(case_id: int, db: Session = Depends(get_db)):
    """
    获取案件详情
    """
    case = get_case_by_id(db=db, case_id=case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="案件不存在")
    return case


# 3️⃣ 普通用户提交案件操作申请（新增/修改/删除）
@router.post("/operations", response_model=CaseOperationOut, status_code=status.HTTP_201_CREATED)
def submit_case_operation(op_in: CaseOperationCreate, db: Session = Depends(get_db)):
    """
    提交案件操作申请
    """
    op = create_case_operation(
        db=db,
        user_id=op_in.user_id,
        operation_type=op_in.operation_type,
        pending_data=op_in.pending_data,
        case_id=op_in.case_id
    )
    return op


# 4️⃣ 查看当前用户提交的案件操作记录
@router.get("/operations/mine", response_model=List[CaseOperationOut])
def get_my_operations(user_id: int, db: Session = Depends(get_db)):
    """
    查询当前用户提交的操作记录
    """
    return list_user_operations(db=db, user_id=user_id)


# 5️⃣ 获取单条操作记录详情（可用于前端查看详细数据）
@router.get("/operations/{operation_id}", response_model=CaseOperationOut)
def get_operation(operation_id: int, db: Session = Depends(get_db)):
    """
    获取单条操作记录
    """
    op = get_operation_by_id(db=db, operation_id=operation_id)
    if not op:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="操作记录不存在")
    return op

# 6️⃣ 获取所有律师列表
@router.get("/users/lawyers", response_model=List[UserOut])
def list_lawyers(db: Session = Depends(get_db)):
    return get_all_lawyers(db)
