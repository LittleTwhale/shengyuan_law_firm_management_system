# api/case_manage.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database.database import get_db
from ..schemas.user import UserOut
from ..schemas.case import CaseOut, CasePageOut, CaseSimpleOut, CaseCreate, CaseUpdate

from ..crud.user import get_all_lawyers
from ..crud.case import list_cases_by_user_role, get_case_by_id, count_cases_by_user_role, create_case, update_case, \
    delete_case

router = APIRouter(
    prefix="/cases",
    tags=["case_manage"]
)


# 1️⃣ 获取正式生效案件列表（分页可选）
@router.get("/", response_model=CasePageOut)
def get_cases(
    user_id: int,
    role: str,
    skip: int = 0,
    limit: int = 100,
    keyword: Optional[str] = None,  # 新增搜索关键词参数
    category: Optional[str] = None,  # 新增案件类别参数
    db: Session = Depends(get_db)
):
    """
    获取案件列表
    """
    cases = list_cases_by_user_role(
        db=db,
        user_id=user_id,
        role=role,
        skip=skip,
        limit=limit,
        keyword=keyword,  # 传递给CRUD函数
        category=category  # 传递给CRUD函数
    )
    total = count_cases_by_user_role(
        db=db,
        user_id=user_id,
        role=role,
        keyword=keyword,  # 传递给统计函数
        category=category  # 传递给统计函数
    )
    cases_simple = [CaseSimpleOut.model_validate(c) for c in cases]
    return {"items": cases_simple, "total": total}


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
@router.post("/case_create", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
def create_new_case(case_in: CaseCreate, db: Session = Depends(get_db)):
    """
    创建新案件
    """
    try:
        new_case = create_case(db=db, case_in=case_in)
        return new_case
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/case_update/{case_id}", response_model=CaseOut)
def update_existing_case(case_id: int, case_in: CaseUpdate, db: Session = Depends(get_db)):
    """
    更新案件
    """
    updated_case = update_case(db=db, case_id=case_id, case_in=case_in)
    if not updated_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="案件不存在")
    return updated_case

@router.delete("/case_delete/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_case(case_id: int, db: Session = Depends(get_db)):
    """
    删除案件（逻辑删除）
    """
    success = delete_case(db=db, case_id=case_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="案件不存在")
    return


# 4️⃣ 获取所有律师列表
@router.get("/users/lawyers", response_model=List[UserOut])
def list_lawyers(db: Session = Depends(get_db)):
    return get_all_lawyers(db)
