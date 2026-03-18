# api/user_profile.py
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..crud import user as user_crud
from ..crud import case as case_crud
from ..crud.case import get_upcoming_events
from ..crud.case_review import count_reviewed_cases
from ..database.database import get_db
from ..schemas.case import CaseStatistics, EventReminderOut
from ..schemas.user import UserOut, ChangePasswordRequest

# 引入当前用户依赖和 User 模型
from .deps import get_current_active_user
from ..models.user import User

router = APIRouter(prefix="/user/profile", tags=["user_profile"])


@router.get("/info", response_model=UserOut)
def get_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户基本信息"""
    return current_user


@router.get("/case-statistics", response_model=CaseStatistics)
def get_case_statistics(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户案件统计数据，支持按年份筛选"""
    # 统计主办案件数
    main_case_count = case_crud.count_main_cases(db, current_user.id, year)
    # 统计主办案件总收费
    total_income = case_crud.sum_main_case_income(db, current_user.id, year)
    # 统计各类案件数量
    case_category_stats = case_crud.count_cases_by_category(db, current_user.id, year)

    result = {
        "main_case_count": main_case_count,
        "total_income": total_income,
        "category_stats": case_category_stats
    }

    # 统计审核案件数
    if current_user.role in ["admin", "owner"]:
        review_count = count_reviewed_cases(db, current_user.id, year)
        result["review_case_count"] = review_count

    return result


@router.put("/change-password")
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """修改密码"""
    user_id = current_user.id
    old_password = data.old_password
    new_password = data.new_password
    return user_crud.change_password(db, user_id, old_password, new_password)


@router.get("/reminders", response_model=List[EventReminderOut])
def get_user_reminders(
        days: int = 7,  # 默认查询7天
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """获取用户的待办事项提醒"""
    return get_upcoming_events(db, current_user.id, days)