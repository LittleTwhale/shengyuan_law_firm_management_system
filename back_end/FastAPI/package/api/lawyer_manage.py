# api/lawyer_manage.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database.database import get_db
from ..schemas.user import UserOut, UserCreate
from ..crud.user import (
    get_users,
    get_ordinary_users,
    create_user,
    update_user,
    get_user_by_accounts
)
from ..models.user import User
from .deps import get_current_active_user

router = APIRouter(
    prefix="/lawyer_manage",
    tags=["lawyer_manage"]
)

# 权限检查工具函数
def has_management_power(current_user: User) -> bool:
    if current_user.role == 'owner':
        return True
    if current_user.role == 'admin':
        # 检查 permissions 字典中的 can_access_admin 字段
        perms = current_user.permissions or {}
        return perms.get("can_access_admin") is True
    return False

# 1. 获取用户列表
@router.get("/users", response_model=List[UserOut])
def list_users(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    获取用户列表
    """
    if current_user.role == "admin":
        return get_ordinary_users(db)
    if current_user.role == "owner":
        return get_users(db)

    # 拒绝普通 user 访问
    raise HTTPException(status_code=403, detail="无权限查看用户列表")


# 2. 新增用户
@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def add_user(
        user_in: UserCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    新增用户
    """
    # 基础权限拦截：拒绝普通用户操作
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="无权限新增用户")

    # 细粒度权限控制：有can_access_admin权限的admin才能创建管理员
    if  user_in.role != "user":
        if not has_management_power(current_user):
            raise HTTPException(status_code=403, detail="权限不足：只有具备后台管理权的管理员才能创建管理员")
        if user_in.role == "owner":
            raise HTTPException(status_code=400, detail="管理员不能创建最高权限用户")

    # 检查账号是否存在
    db_user = get_user_by_accounts(db, user_in.accounts)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="账号已存在"
        )
    user = create_user(db, user_in)
    return user


# 3. 修改用户信息
@router.put("/users/{user_id}", response_model=UserOut)
def edit_user(
        user_id: int,
        update_data: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    修改用户信息（支持修改姓名、角色、职位、密码等）
    """
    # 基础权限拦截
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="无权限修改用户信息")

    # 先查询出目标用户，用于后续权限判断
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # admin不能修改owner信息
    if user.role == "owner" and current_user.role != "owner":
        raise HTTPException(status_code=403, detail="权限不足：您没有修改最高权限用户的权限")
    # 如果尝试修改角色为 admin
    new_role = update_data.get("role")
    if new_role == "admin":
        # 只有 owner 或 有权的 admin 才能授权
        if not has_management_power(current_user):
            raise HTTPException(status_code=403, detail="权限不足：您没有分配管理员角色的权限")

    # 防止提权到 owner
    if new_role == "owner" and current_user.role != "owner":
        raise HTTPException(status_code=403, detail="禁止非法提权")

    updated_user = update_user(db, user_id, update_data)
    return updated_user


# 4. 删除用户
@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    删除用户
    """
    # 基础权限拦截
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="无权限删除用户")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 权限控制：admin只能删除普通user
    if current_user.role == "admin" and user.role != "user":
        raise HTTPException(status_code=403, detail="无权限删除非普通用户")

    db.delete(user)
    db.commit()
    return None