# crud/error_analysis_crud.py
"""
错误分析记录 CRUD 操作
包含创建、查询（分页）、查重、删除等操作
"""
from typing import Optional, Tuple, List
from datetime import datetime, timedelta

from sqlalchemy import desc, and_
from sqlalchemy.orm import Session

from ..models.error_analysis_model import ErrorAnalysis


# ==========================================
# 创建
# ==========================================
def create_error_analysis(db: Session, data: dict) -> ErrorAnalysis:
    """
    创建一条新的错误分析记录
    data 应包含模型各字段，如 error_type, error_message, user_accounts 等
    """
    record = ErrorAnalysis(**data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ==========================================
# 查询（单条）
# ==========================================
def get_analysis(db: Session, analysis_id: int) -> Optional[ErrorAnalysis]:
    """根据 ID 获取分析记录"""
    return db.query(ErrorAnalysis).filter(ErrorAnalysis.id == analysis_id).first()


# ==========================================
# 查询（分页列表）
# ==========================================
def get_analyses(
    db: Session,
    user_accounts: Optional[str] = None,
    analysis_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[int, List[ErrorAnalysis]]:
    """
    获取错误分析记录列表，支持按用户和状态筛选

    Args:
        db: 数据库 Session
        user_accounts: 如果提供，只返回该用户的记录
        analysis_status: 可选的状态筛选
        skip: 分页偏移
        limit: 每页数量

    Returns:
        (总记录数, 当前页记录列表)
    """
    query = db.query(ErrorAnalysis)

    # 按用户筛选（未登录匿名错误也包含）
    if user_accounts:
        query = query.filter(ErrorAnalysis.user_accounts == user_accounts)

    # 按状态筛选
    if analysis_status:
        query = query.filter(ErrorAnalysis.analysis_status == analysis_status)

    # 按时间倒序排列（最新的在前）
    query = query.order_by(desc(ErrorAnalysis.created_at))

    # 统计总数
    total = query.count()

    # 分页
    items = query.offset(skip).limit(limit).all()

    return total, items


# ==========================================
# 查询（管理员视角 — 查看所有记录）
# ==========================================
def get_all_analyses_admin(
    db: Session,
    analysis_status: Optional[str] = None,
    error_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[int, List[ErrorAnalysis]]:
    """
    管理员查看所有错误分析记录，支持按状态和异常类型筛选
    """
    query = db.query(ErrorAnalysis)

    if analysis_status:
        query = query.filter(ErrorAnalysis.analysis_status == analysis_status)
    if error_type:
        query = query.filter(ErrorAnalysis.error_type == error_type)

    query = query.order_by(desc(ErrorAnalysis.created_at))
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return total, items


# ==========================================
# 更新分析结果
# ==========================================
def update_analysis_result(
    db: Session,
    analysis_id: int,
    analysis_result: str,
    analysis_status: str = "completed",
) -> Optional[ErrorAnalysis]:
    """
    DeepSeek 分析完成后，更新分析结果和状态
    """
    record = db.query(ErrorAnalysis).filter(ErrorAnalysis.id == analysis_id).first()
    if not record:
        return None

    record.analysis_result = analysis_result
    record.analysis_status = analysis_status
    record.analyzed_at = datetime.now()
    db.commit()
    db.refresh(record)
    return record


# ==========================================
# 标记分析失败
# ==========================================
def mark_analysis_failed(db: Session, analysis_id: int, error_msg: str) -> Optional[ErrorAnalysis]:
    """标记某条分析记录为失败状态"""
    record = db.query(ErrorAnalysis).filter(ErrorAnalysis.id == analysis_id).first()
    if not record:
        return None

    record.analysis_status = "failed"
    record.analysis_error = error_msg[:500]
    db.commit()
    db.refresh(record)
    return record


# ==========================================
# 状态更新（processing）
# ==========================================
def mark_analysis_processing(db: Session, analysis_id: int) -> Optional[ErrorAnalysis]:
    """标记开始处理（防止重复消费）"""
    record = db.query(ErrorAnalysis).filter(ErrorAnalysis.id == analysis_id).first()
    if not record:
        return None
    record.analysis_status = "processing"
    db.commit()
    return record


# ==========================================
# 去重检查
# ==========================================
def find_recent_analysis_by_fingerprint(
    db: Session, fingerprint: str, within_minutes: int = 60
) -> Optional[ErrorAnalysis]:
    """
    查找最近 N 分钟内是否有相同指纹的分析记录（用于去重）
    如果找到且已完成，直接复用，不再调 DeepSeek
    """
    cutoff = datetime.now() - timedelta(minutes=within_minutes)
    return (
        db.query(ErrorAnalysis)
        .filter(
            and_(
                ErrorAnalysis.error_fingerprint == fingerprint,
                ErrorAnalysis.created_at >= cutoff,
                ErrorAnalysis.analysis_status == "completed",
            )
        )
        .first()
    )


# ==========================================
# 删除
# ==========================================
def delete_analysis(db: Session, analysis_id: int) -> bool:
    """删除一条分析记录"""
    record = db.query(ErrorAnalysis).filter(ErrorAnalysis.id == analysis_id).first()
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True


# ==========================================
# 未通知记录查询 & 标记已通知（兜底轮询用）
# ==========================================
def get_unnotified_analyses(
    db: Session,
    user_accounts: Optional[str] = None,
    limit: int = 10,
) -> List[ErrorAnalysis]:
    """
    查询当前用户未通知的已完成分析记录（按时间倒序）
    用于前端后台轮询兜底，覆盖非 500 响应场景。
    """
    query = db.query(ErrorAnalysis).filter(
        ErrorAnalysis.notified == False,
        ErrorAnalysis.analysis_status == "completed",
    )
    if user_accounts:
        query = query.filter(ErrorAnalysis.user_accounts == user_accounts)
    query = query.order_by(desc(ErrorAnalysis.created_at)).limit(limit)
    return query.all()


def mark_analyses_notified(db: Session, analysis_ids: List[int]) -> int:
    """
    批量标记分析记录为已通知
    返回实际更新的记录数
    """
    if not analysis_ids:
        return 0
    updated = (
        db.query(ErrorAnalysis)
        .filter(ErrorAnalysis.id.in_(analysis_ids))
        .update({"notified": True}, synchronize_session="fetch")
    )
    db.commit()
    return updated


# ==========================================
# 自动清理旧记录（保留 N 天）
# ==========================================
def clean_old_analyses(db: Session, retention_days: int = 30) -> int:
    """
    清理超过保留天数的旧记录
    返回删除的记录数
    """
    cutoff = datetime.now() - timedelta(days=retention_days)
    deleted = (
        db.query(ErrorAnalysis)
        .filter(ErrorAnalysis.created_at < cutoff)
        .delete(synchronize_session="fetch")
    )
    db.commit()
    return deleted
