# crud/user.py
from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from ..core.security import verify_password,hash_password
from ..models.user import User, UserSchedule
from ..schemas.case import UserScheduleUpdate, UserScheduleCreate
from ..schemas.user import UserCreate, UserPermissionUpdate
from typing import Optional, List, cast


def get_user_by_accounts(db: Session, accounts: str) -> Optional[User]:
    """
    根据账号查询用户
    """
    return db.query(User).filter(User.accounts == accounts).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    根据ID查询用户
    """
    return db.query(User).filter(User.id == user_id).first()

def authenticate_user(db: Session, accounts: str, password: str) -> Optional[User]:
    """
    用户登录验证
    """
    user = get_user_by_accounts(db, accounts)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def create_user(db: Session, user_in: UserCreate) -> User:
    """
    创建新用户
    """
    hashed_password = hash_password(user_in.password)
    db_user = User(
        accounts=user_in.accounts,
        password_hash=hashed_password,
        real_name=user_in.real_name,
        role=user_in.role,
        position=user_in.position
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def change_password(db: Session, user_id: int, old_password: str, new_password: str) -> dict:
    """修改密码"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 验证旧密码
    if not verify_password(old_password, str(user.password_hash)):
        raise HTTPException(status_code=400, detail="旧密码不正确")

    # 更新密码
    user.password_hash = hash_password(new_password)
    db.commit()
    return {"message": "密码修改成功"}

def update_user(db: Session, user_id: int, update_data: dict) -> Optional[User]:
    """
    修改用户信息
    """
    user : Optional[User] = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    for key, value in update_data.items():
        if key == "password":  # 如果修改密码
            value = hash_password(value)
            setattr(user, "password_hash", value)
        elif hasattr(user, key):
            setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user

def get_users(db: Session) -> List[User]:
    """
    获取用户列表
    """
    users = db.query(User).all()
    return cast(List[User], users)


def get_users_paginated(db: Session, skip: int = 0, limit: int = 20, keyword: Optional[str] = None):
    """
    获取分页用户列表（支持按姓名或账号模糊搜索）
    """
    query = db.query(User)

    # 如果有搜索关键字，执行模糊匹配
    if keyword:
        search_term = f"%{keyword}%"
        query = query.filter(
            or_(
                User.real_name.ilike(search_term),  # ilike 支持不区分大小写
                User.accounts.ilike(search_term)
            )
        )

    # 获取符合条件的总条数
    total = query.count()

    # 获取当前页的数据
    users = query.offset(skip).limit(limit).all()

    return users, total

def get_ordinary_users(db: Session) -> List[User]:
    """
    获取普通用户列表
    """
    # 筛选条件：角色为 user 或 admin（排除 owner）
    users = db.query(User).filter(
        User.role.in_(["user", "admin"])  # 包含普通用户和管理员
    ).all()
    return cast(List[User], users)

def get_all_lawyers(db: Session):
    """
    获取所有律师
    """
    return (
        db.query(User)
        .filter(User.role != "owner")  # 排除系统设计者
        .all()
    )

def get_user_id_by_name(db: Session, real_name: str) -> Optional[int]:
    """通过姓名查询用户ID（假设无重名）"""
    user = db.query(User).filter(User.real_name == real_name).first()
    return user.id if user else None


def update_user_permissions(db: Session, user_id: int, permissions: UserPermissionUpdate):
    """更新用户的权限"""
    # 1. 查询用户
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None

    # 2. 获取当前的权限字典 (如果为None则初始化为空字典)
    current_permissions = db_user.permissions or {}

    # 3. 更新权限
    # 遍历传入的 permissions (exclude_unset=True 保证只更新前端传来的字段)
    update_data = permissions.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        current_permissions[key] = value

    # 4. 显式重新赋值 (这对于触发 SQLAlchemy 的 JSON 字段更新很重要)
    # 这是一个常见的坑：直接修改 JSON 内部属性可能不会被 ORM 检测到变化
    db_user.permissions = dict(current_permissions)
    flag_modified(db_user, "permissions")

    # 5. 提交事务
    db.add(db_user)  # 确保对象在 session 中
    db.commit()
    db.refresh(db_user)
    return db_user


# ==========================================
# 用户自定义日程 (UserSchedules) 相关 CRUD
# ==========================================

def create_user_schedule(db: Session, user_id: int, schedule_in: UserScheduleCreate) -> UserSchedule:
    """
    创建用户自定义日程
    """
    db_schedule = UserSchedule(
        user_id=user_id,
        title=schedule_in.title,
        event_date=schedule_in.event_date,
        description=schedule_in.description,
        related_case_id=schedule_in.related_case_id
    )
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule


def update_user_schedule(
        db: Session,
        schedule_id: int,
        user_id: int,
        schedule_in: UserScheduleUpdate
) -> Optional[UserSchedule]:
    """
    修改用户自定义日程
    注意：加入了 user_id 校验，防止越权修改其他人的日程
    """
    db_schedule = db.query(UserSchedule).filter(
        UserSchedule.id == schedule_id,
        UserSchedule.user_id == user_id
    ).first()

    if not db_schedule:
        return None

    # exclude_unset=True 确保只更新前端传过来的非空/已修改字段
    update_data = schedule_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_schedule, key, value)

    db.commit()
    db.refresh(db_schedule)
    return db_schedule


def delete_user_schedule(db: Session, schedule_id: int, user_id: int) -> bool:
    """
    删除用户自定义日程
    注意：加入了 user_id 校验，防止越权删除
    """
    db_schedule = db.query(UserSchedule).filter(
        UserSchedule.id == schedule_id,
        UserSchedule.user_id == user_id
    ).first()

    if not db_schedule:
        return False

    db.delete(db_schedule)
    db.commit()
    return True