# api/user_profile.py
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from ..models.case import Case
from ..crud import user as user_crud
from ..crud import case as case_crud
from ..crud.case import get_upcoming_events
from ..crud.case_review import count_reviewed_cases
from ..database.database import get_db
from ..schemas.case import CaseStatistics, EventReminderOut, UserScheduleCreate, UserScheduleUpdate
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


@router.get("/reminders")
def get_user_reminders(
        days: int = 7,
        main_lawyer_id: Optional[int] = None,  # 接收主办律师筛选参数
        relation: str = "all",
        skip: int = 0,  # 接收分页参数
        limit: int = 20,  # 接收分页参数
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """获取用户的待办事项提醒（支持过滤和分页）"""
    has_bank_event_perm = current_user.permissions.get("can_view_all_bank_events",
                                                       False) if current_user.permissions else False

    return get_upcoming_events(
        db=db,
        user_id=current_user.id,
        days=days,
        can_view_all_bank_events=has_bank_event_perm,
        main_lawyer_id=main_lawyer_id,
        relation_filter=relation,
        skip=skip,
        limit=limit
    )


@router.get("/my-cases/simple")
def get_my_simple_cases(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    获取当前用户主办或协办的所有案件简要信息（用于下拉列表）
    """
    # 1. 查询时使用 joinedload 预加载 parties
    cases = db.query(Case).options(
        joinedload(Case.parties)
    ).filter(
        Case.is_deleted == False,
        or_(
            Case.main_lawyer_id == current_user.id,
            Case.assistant_lawyer_id == current_user.id,
            Case.assistant_lawyer_2_id == current_user.id,
            Case.execution_lawyer_id == current_user.id,
            Case.execution_assistant_id == current_user.id
        )
    ).order_by(Case.created_at.desc()).all()

    # 2. 组装为前端需要的简单字典列表
    result = []
    for c in cases:
        # 动态获取当事人列表中的委托人名称 (可能有多个委托人)
        clients = [p.name for p in c.parties if p.party_type and '委托' in p.party_type and p.name]

        # 将多个委托人名字用顿号拼接。
        real_client_name = "、".join(clients) if clients else ""

        result.append({
            "case_id": c.case_id,
            "case_number": c.case_number,
            "client_name": real_client_name
        })

    return result

# 1. 创建自定义日程
@router.post("/reminders/custom")
def create_custom_schedule(
    schedule: UserScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建用户自定义待办事项"""
    return user_crud.create_user_schedule(db, current_user.id, schedule)

# 2. 修改自定义日程
@router.put("/reminders/custom/{schedule_id}")
def update_custom_schedule(
    schedule_id: int,
    schedule: UserScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """修改自定义待办事项"""
    return user_crud.update_user_schedule(db, schedule_id, current_user.id, schedule)

# 3. 删除自定义日程
@router.delete("/reminders/custom/{schedule_id}")
def delete_custom_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除自定义待办事项"""
    success = user_crud.delete_user_schedule(db, schedule_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="日程不存在或无权删除")
    return {"message": "删除成功"}