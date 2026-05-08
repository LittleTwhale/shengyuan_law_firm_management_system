# core/user_cache.py
"""
用户信息缓存模块
为了提高日志记录的性能，避免每次请求都查询数据库
"""
import time
from typing import Optional, Dict, Tuple
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from .config import SECRET_KEY, ALGORITHM
from ..database.database import SessionLocal
from ..crud import user as crud_user


class UserInfoCache:
    """用户信息缓存类"""

    def __init__(self, cache_ttl: int = 300):  # 缓存5分钟
        self._cache: Dict[str, Tuple[str, float]] = {}  # {accounts: (display_name, expire_time)}
        self._cache_ttl = cache_ttl

    def get_user_display_name(self, token: str) -> str:
        """
        从token获取用户显示名称，使用缓存机制

        Args:
            token: JWT token字符串

        Returns:
            str: 用户显示名称，失败时返回"匿名用户"
        """
        try:
            # 解码token获取用户账号
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_accounts = payload.get("sub")
            if not user_accounts:
                return "匿名用户"

            # 检查缓存
            current_time = time.time()
            if user_accounts in self._cache:
                display_name, expire_time = self._cache[user_accounts]
                if current_time < expire_time:
                    return display_name
                else:
                    # 缓存过期，删除
                    del self._cache[user_accounts]

            # 缓存未命中或已过期，查询数据库
            db = SessionLocal()
            try:
                user = crud_user.get_user_by_accounts(db, accounts=user_accounts)
                if user:
                    display_name = user.real_name if user.real_name else user.accounts
                    # 更新缓存
                    self._cache[user_accounts] = (display_name, current_time + self._cache_ttl)
                    return display_name
                else:
                    return "未知用户"
            except Exception:
                return "查询失败"
            finally:
                db.close()

        except (JWTError, Exception):
            return "匿名用户"

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()

    def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        current_time = time.time()
        active_entries = sum(1 for _, expire_time in self._cache.values() if current_time < expire_time)
        return {
            "total_entries": len(self._cache),
            "active_entries": active_entries,
            "cache_hit_potential": active_entries > 0
        }


# 创建全局缓存实例
user_cache = UserInfoCache()