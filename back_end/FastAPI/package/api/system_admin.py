# api/system_admin.py
"""
系统管理相关的API端点
包括缓存管理等功能
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..api.deps import get_current_user
from ..models.user import User
from ..core.user_cache import user_cache

router = APIRouter(prefix="/system", tags=["系统管理"])


@router.post("/clear-user-cache")
def clear_user_cache(
    current_user: User = Depends(get_current_user),
):
    """
    清空用户信息缓存
    需要管理员权限
    """
    # 检查用户权限
    if current_user.role not in ['admin', 'owner']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限执行此操作"
        )

    # 清空缓存
    user_cache.clear_cache()

    return {
        "code": 200,
        "message": "用户缓存已清空",
        "data": None
    }


@router.get("/cache-stats")
def get_cache_stats(
    current_user: User = Depends(get_current_user),
):
    """
    获取缓存统计信息
    需要管理员权限
    """
    # 检查用户权限
    if current_user.role not in ['admin', 'owner']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限执行此操作"
        )

    stats = user_cache.get_cache_stats()

    return {
        "code": 200,
        "message": "获取缓存统计成功",
        "data": stats
    }