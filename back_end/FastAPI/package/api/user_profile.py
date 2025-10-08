# api/user_profile.py
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from ..crud import user as user_crud
from ..crud import case as case_crud
from ..crud.case_review import count_reviewed_cases
from ..database.database import get_db
from ..schemas.case import CaseStatistics
from ..schemas.user import UserOut, ChangePasswordRequest

router = APIRouter(prefix="/user/profile", tags=["user_profile"])


@router.get("/info", response_model=UserOut)
def get_user_info(db: Session = Depends(get_db), user_id: int = None):
    """获取当前用户基本信息"""
    if not user_id:
        raise HTTPException(status_code=400, detail="用户ID不能为空")
    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.get("/case-statistics", response_model=CaseStatistics)
def get_case_statistics(user_id: int, db: Session = Depends(get_db)):
    """获取用户案件统计数据"""
    # 统计主办案件数
    main_case_count = case_crud.count_main_cases(db, user_id)
    # 统计主办案件总收费
    total_income = case_crud.sum_main_case_income(db, user_id)
    # 统计各类案件数量
    case_category_stats = case_crud.count_cases_by_category(db, user_id)

    result = {
        "main_case_count": main_case_count,
        "total_income": total_income,
        "category_stats": case_category_stats
    }

    # 如果是管理员，添加审核案件数
    user = user_crud.get_user_by_id(db, user_id)
    if user.role in ["admin", "owner"]:
        review_count = count_reviewed_cases(db, user_id)
        result["review_case_count"] = review_count

    return result


@router.put("/change-password")
def change_password(data: ChangePasswordRequest, db: Session = Depends(get_db)):
    """修改密码"""
    user_id = data.user_id
    old_password = data.old_password
    new_password = data.new_password
    return user_crud.change_password(db, user_id, old_password, new_password)