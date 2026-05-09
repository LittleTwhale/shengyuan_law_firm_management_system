# api/system_admin.py
"""
系统管理相关的API端点
包括缓存管理等功能
"""
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from ..api.deps import get_current_user
from ..core.user_cache import user_cache
from ..models.user import User

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


@router.get("/export-log")
def export_system_log(
        date: str,
        current_user: User = Depends(get_current_user),
):
    """
    按日期导出系统日志
    需要管理员权限
    参数 date 格式：'2023-10-25'
    """
    # 检查用户权限
    if current_user.role not in ['admin', 'owner']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限执行此操作"
        )

    try:
        # 解析日期字符串
        target_date = datetime.strptime(date, "%Y-%m-%d")
        year_str = target_date.strftime("%Y")
        month_str = target_date.strftime("%m")
        day_str = target_date.strftime("%d")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="日期格式错误，应为 YYYY-MM-DD"
        )

    # 这里的 LOG_ROOT 必须从你的 config.py 里导入，和 logger.py 里使用的是同一个变量
    # 如果没有导出，你可以临时写死绝对/相对路径，例如 base_dir = "logs"
    from ..core.config import LOG_ROOT

    # 根据 logger.py 里的目录逻辑拼接路径：LOG_ROOT/YYYY/MM/DD.log
    log_file_path = os.path.join(LOG_ROOT, year_str, month_str, f"{day_str}.log")

    # 检查文件是否存在
    if not os.path.exists(log_file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到 {date} 的日志文件"
        )

    # 使用生成器按块读取文件
    def iterfile():
        with open(log_file_path, mode="rb") as file_like:
            yield from file_like

    return StreamingResponse(
        iterfile(),
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=system_log_{date}.log"
        }
    )