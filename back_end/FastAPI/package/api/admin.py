# api/admin.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import database
from ..schemas.user import UserOut, UserPermissionUpdate
from ..crud.user import get_users, update_user_permissions

router = APIRouter(prefix="/admin/system", tags=["admin_system"])


def check_super_admin(user_id: int, role: str):
    """
    检查操作者是否为超级管理员 (Owner 且 ID 为 1)
    注意：这是基于前端传参的校验，安全性依赖于前端逻辑（和你现有项目一致）
    """
    # 强制要求 role 为 owner 且 user_id 为 1
    if role != 'owner' or str(user_id) != '1':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )


# 1. 获取所有用户及其权限列表
@router.get("/users_with_permissions", response_model=List[UserOut])
def get_users_with_permissions(
        # 操作者的身份信息（由前端传递）
        current_user_id: int,
        current_user_role: str,

        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(database.get_db)
):
    # 1. 权限校验
    check_super_admin(current_user_id, current_user_role)

    # 2. 获取用户列表 (复用 CRUD 中的 get_users)
    # UserOut schema 会自动包含 permissions 字段
    users = get_users(db)
    # 简单的切片分页
    return users[skip: skip + limit]


# 2. 更新指定用户的权限
@router.put("/permissions/{target_user_id}", response_model=UserOut)
def update_permissions(
        target_user_id: int,
        permission_update: UserPermissionUpdate,

        # 操作者的身份信息（由前端传递）
        current_user_id: int,
        current_user_role: str,

        db: Session = Depends(database.get_db)
):
    # 1. 权限校验
    check_super_admin(current_user_id, current_user_role)

    # 2. 禁止修改 Owner (ID=1) 的权限，防止把自己锁死
    if str(target_user_id) == '1':
        raise HTTPException(status_code=400, detail="无法修改超级管理员的权限")

    # 3. 执行更新
    updated_user = update_user_permissions(db, target_user_id, permission_update)

    if not updated_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return updated_user