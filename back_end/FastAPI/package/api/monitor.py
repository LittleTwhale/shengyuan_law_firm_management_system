# api/monitor.py
"""
服务器资源监控 API
提供 CPU、内存、磁盘（C/D 盘）、网络、磁盘 I/O、QPS、活跃用户的实时数据采集
以及全站数据概览（案件、卷宗、律师数量）
"""
import time
import psutil
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..api.deps import get_current_user
from ..database.database import get_db
from ..models.user import User
from ..models.case import Case
from ..models.electronic_volume_model import CaseVolume
from ..utils.request_tracker import request_tracker

router = APIRouter(prefix="/monitor", tags=["System Monitor"])

# ── 磁盘 I/O 速率计算的缓存 ──
_prev_disk_io = {}  # {disk_name: (prev_read_bytes, prev_write_bytes, prev_time)}


def _get_disk_info(disk_path):
    """获取指定磁盘分区的使用情况"""
    try:
        usage = psutil.disk_usage(disk_path)
        return {
            "total_gb": round(usage.total / (1024 ** 3), 1),
            "used_gb": round(usage.used / (1024 ** 3), 1),
            "free_gb": round(usage.free / (1024 ** 3), 1),
            "percent": usage.percent,
        }
    except Exception:
        return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "percent": 0}


def _get_network_info():
    """获取网络累计收发数据"""
    try:
        counters = psutil.net_io_counters()
        return {
            "bytes_sent": counters.bytes_sent,  # 去掉了 _mb 后缀，不除以 1024
            "bytes_recv": counters.bytes_recv,
            "packets_sent": counters.packets_sent,
            "packets_recv": counters.packets_recv,
        }
    except Exception:
        return {"bytes_sent": 0, "bytes_recv": 0, "packets_sent": 0, "packets_recv": 0}


def _get_disk_io_rates():
    """
    获取系统总体磁盘 I/O 读写速率 (KB/s)
    通过对比两次调用的累计字节差来计算
    """
    global _prev_disk_io
    try:
        counters = psutil.disk_io_counters()
        now = time.time()
        key = "total"
        prev = _prev_disk_io.get(key)

        if prev is None:
            _prev_disk_io[key] = (counters.read_bytes, counters.write_bytes, now)
            return {"read_kbps": 0, "write_kbps": 0}

        elapsed = now - prev[2]
        if elapsed <= 0:
            return {"read_kbps": 0, "write_kbps": 0}

        read_delta = counters.read_bytes - prev[0]
        write_delta = counters.write_bytes - prev[1]
        _prev_disk_io[key] = (counters.read_bytes, counters.write_bytes, now)

        return {
            "read_kbps": round(read_delta / 1024 / elapsed, 1),
            "write_kbps": round(write_delta / 1024 / elapsed, 1),
        }
    except Exception:
        return {"read_kbps": 0, "write_kbps": 0}


@router.get("/system-info")
def get_system_info(current_user: User = Depends(get_current_user)):
    """
    获取服务器实时资源使用情况
    返回 CPU、内存、C/D 盘、网络、磁盘 I/O、QPS、活跃用户数
    """
    cpu_percent = psutil.cpu_percent(interval=0.3)

    memory = psutil.virtual_memory()
    mem_info = {
        "total_gb": round(memory.total / (1024 ** 3), 1),
        "used_gb": round(memory.used / (1024 ** 3), 1),
        "available_gb": round(memory.available / (1024 ** 3), 1),
        "percent": memory.percent,
    }

    disk_c = _get_disk_info("C:\\")
    disk_d = _get_disk_info("D:\\")
    network_info = _get_network_info()
    disk_io = _get_disk_io_rates()

    return {
        "code": 200,
        "message": "获取系统资源信息成功",
        "data": {
            "cpu": {"percent": cpu_percent},
            "memory": mem_info,
            "disk_c": disk_c,
            "disk_d": disk_d,
            "network": network_info,
            "disk_io": disk_io,
            "qps": request_tracker.get_qps(),
            "active_users": request_tracker.get_active_user_count(minutes=15),
        },
    }


@router.get("/site-stats")
def get_site_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取全站数据概览（静态数据，无需高频刷新）
    返回案件数、电子卷宗数、律师人数
    """
    case_count = db.query(func.count(Case.case_id)).filter(Case.is_deleted == False).scalar() or 0
    volume_count = db.query(func.count(CaseVolume.id)).scalar() or 0
    lawyer_count = db.query(func.count(User.id)).filter(User.role.in_(['user', 'admin', 'owner'])).scalar() - 1 or 0

    return {
        "code": 200,
        "message": "获取全站数据概览成功",
        "data": {
            "cases": case_count,
            "volumes": volume_count,
            "lawyers": lawyer_count,
        },
    }
