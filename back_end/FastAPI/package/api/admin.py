# api/admin.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from ..database import database
from ..schemas.user import UserOut, UserPermissionUpdate
from ..crud.user import get_users_paginated, update_user_permissions
from ..models.user import User
from .deps import get_current_active_user

router = APIRouter(prefix="/admin/system", tags=["admin_system"])


def check_admin_permission(current_user: User, target_user: User = None):
    """
    校验后台管理权限
    1. owner 拥有最高权限
    2. 拥有 can_access_admin=True 的 admin 也有后台权限
    3. 如果操作涉及具体用户(target_user)，admin 不能操作 owner
    """
    is_owner = current_user.role == 'owner'

    # 检查 permissions 是否为字典并且包含 can_access_admin
    has_admin_perm = False
    if current_user.permissions and isinstance(current_user.permissions, dict):
        has_admin_perm = current_user.permissions.get("can_access_admin") is True

    is_authorized_admin = (current_user.role == 'admin' and has_admin_perm)

    # 1. 基础入口权限校验
    if not (is_owner or is_authorized_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足：您没有后台管理权限"
        )

    # 2. 防越权保护：如果传入了目标操作用户，确保 admin 不能操作 owner
    if target_user:
        if current_user.role != 'owner' and target_user.role == 'owner':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="越权操作：管理员无权修改最高权限(owner)账户的权限"
            )


# 1. 获取所有用户及其权限列表
@router.get("/users_with_permissions")
def get_users_with_permissions(
        skip: int = 0,
        limit: int = 20,  # 默认值
        keyword: Optional[str] = None,  # 接收前端的搜索词
        db: Session = Depends(database.get_db),
        current_user: User = Depends(get_current_active_user)
):
    # 1. 权限校验 (列表接口，不需要传入目标用户)
    check_admin_permission(current_user)

    # 2. 调用新的分页查询函数
    users, total = get_users_paginated(db, skip=skip, limit=limit, keyword=keyword)

    # 3. 构造分页返回结构
    return {
        "items": users,
        "total": total
    }


# 2. 更新指定用户的权限
@router.put("/permissions/{target_user_id}", response_model=UserOut)
def update_permissions(
        target_user_id: int,
        permission_update: UserPermissionUpdate,
        db: Session = Depends(database.get_db),
        current_user: User = Depends(get_current_active_user)
):
    # 1. 先从数据库查出被操作的目标用户
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 2. 细粒度权限校验（带入目标用户，触发防越权保护）
    check_admin_permission(current_user, target_user)

    # 3. 细粒度权限校验：Owner 才能分配或撤销后台管理权
    if permission_update.can_access_admin is not None:
        if current_user.role != 'owner':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="越权操作：仅 Owner 有权分配或撤销后台管理权"
            )

    # 4. 防止 Owner 误操作锁死自己
    if current_user.id == target_user_id and current_user.role == 'owner':
        if permission_update.can_access_admin is False:
            raise HTTPException(status_code=400, detail="Owner 不能撤销自己的后台管理权限")

    # 4. 执行更新
    updated_user = update_user_permissions(db, target_user_id, permission_update)

    return updated_user