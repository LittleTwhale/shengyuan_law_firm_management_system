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

    # 细粒度权限控制：admin只能创建普通user
    if current_user.role == "admin" and user_in.role != "user":
        raise HTTPException(status_code=403, detail="无权限新增非普通用户")

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

    # 权限控制：admin只能操作现有的普通user
    if current_user.role == "admin" and user.role != "user":
        raise HTTPException(status_code=403, detail="无权限操作非普通用户")

    # 防止提权：admin 不能把用户角色修改为 admin 或 owner
    if current_user.role == "admin" and update_data.get("role") and update_data.get("role") != "user":
        raise HTTPException(status_code=403, detail="无权限将用户修改为高级角色")

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