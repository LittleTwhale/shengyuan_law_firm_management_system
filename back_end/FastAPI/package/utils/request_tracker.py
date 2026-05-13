# utils/request_tracker.py
"""
请求追踪模块 —— 用于 QPS 计算和在线活跃用户统计
纯内存实现，线程安全
"""
import time
import threading
from collections import deque
from typing import Set, Dict


class RequestTracker:
    """线程安全的请求追踪器（单例模式）"""

    def __init__(self):
        self._lock = threading.Lock()
        # QPS 追踪：记录最近 1 秒内的请求时间戳
        self._request_timestamps: deque = deque()
        # 活跃用户追踪：{accounts: 最后活跃时间戳}
        self._active_users: Dict[str, float] = {}

    def record_request(self, accounts: str = None):
        """记录一次 API 请求"""
        now = time.time()
        with self._lock:
            # 记录请求时间戳（用于 QPS）
            self._request_timestamps.append(now)
            # 清理超过 1 秒的旧时间戳
            cutoff = now - 1.0
            while self._request_timestamps and self._request_timestamps[0] < cutoff:
                self._request_timestamps.popleft()

            # 记录用户活跃时间
            if accounts:
                self._active_users[accounts] = now

    def get_qps(self) -> float:
        """获取当前 QPS（过去 1 秒的请求数）"""
        now = time.time()
        with self._lock:
            cutoff = now - 1.0
            while self._request_timestamps and self._request_timestamps[0] < cutoff:
                self._request_timestamps.popleft()
            return round(len(self._request_timestamps), 1)

    def get_active_user_count(self, minutes: int = 15) -> int:
        """获取最近 N 分钟内有请求的独立用户数"""
        now = time.time()
        cutoff = now - (minutes * 60)
        with self._lock:
            # 清理过期用户
            expired = [a for a, t in self._active_users.items() if t < cutoff]
            for a in expired:
                del self._active_users[a]
            return len(self._active_users)


# 全局单例
request_tracker = RequestTracker()
