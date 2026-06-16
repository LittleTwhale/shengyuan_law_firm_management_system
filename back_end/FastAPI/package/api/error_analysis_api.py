# api/error_analysis_api.py
"""
错误分析结果查询 API

用户可以通过此 API 查看由 DeepSeek 自动分析的服务端错误报告。
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..api.deps import get_current_active_user
from ..database.database import get_db
from ..models.user import User
from ..crud.error_analysis_crud import (
    get_analysis,
    get_analyses,
    get_all_analyses_admin,
    delete_analysis,
    clean_old_analyses,
)

router = APIRouter(prefix="/error-analyses", tags=["Error Analysis"])


# =================================================================
#  GET /api/error-analyses — 当前用户自己的错误分析列表
# =================================================================
@router.get("")
def list_my_analyses(
    analysis_status: str = Query(None, description="筛选状态: pending/processing/completed/failed"),
    skip: int = Query(0, ge=0, description="分页偏移"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取当前用户触发的错误分析记录列表（分页，按时间倒序）
    - 管理员/owner 可以查看所有记录（加 ?scope=admin 参数）
    - 普通用户只能查看自己的记录
    """
    user_accounts = current_user.accounts

    total, items = get_analyses(
        db=db,
        user_accounts=user_accounts,
        analysis_status=analysis_status,
        skip=skip,
        limit=limit,
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [
            {
                "id": item.id,
                "error_type": item.error_type,
                "error_message": item.error_message[:200],
                "request_method": item.request_method,
                "request_path": item.request_path,
                "user_real_name": item.user_real_name,
                "analysis_status": item.analysis_status,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "analyzed_at": item.analyzed_at.isoformat() if item.analyzed_at else None,
            }
            for item in items
        ],
    }


# =================================================================
#  GET /api/error-analyses/admin — 管理员查看所有
# =================================================================
@router.get("/admin")
def list_all_analyses_admin(
    analysis_status: str = Query(None, description="筛选状态"),
    error_type: str = Query(None, description="按异常类型筛选"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """管理员/owner 查看所有用户的错误分析记录"""
    if current_user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="权限不足，仅管理员可查看全部记录")

    total, items = get_all_analyses_admin(
        db=db,
        analysis_status=analysis_status,
        error_type=error_type,
        skip=skip,
        limit=limit,
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [
            {
                "id": item.id,
                "error_type": item.error_type,
                "error_message": item.error_message[:200],
                "request_method": item.request_method,
                "request_path": item.request_path,
                "user_accounts": item.user_accounts,
                "user_real_name": item.user_real_name,
                "user_ip": item.user_ip,
                "analysis_status": item.analysis_status,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "analyzed_at": item.analyzed_at.isoformat() if item.analyzed_at else None,
            }
            for item in items
        ],
    }


# =================================================================
#  GET /api/error-analyses/{analysis_id} — 单条详情
# =================================================================
@router.get("/{analysis_id}")
def get_analysis_detail(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取单条错误分析的完整详情（包含 DeepSeek 的分析建议）
    - 普通用户只能查看自己的
    - 管理员/owner 可以查看任何人的
    """
    record = get_analysis(db, analysis_id)
    if not record:
        raise HTTPException(status_code=404, detail="分析记录不存在")

    # 权限检查：普通用户只能看自己的
    is_admin = current_user.role in ("admin", "owner")
    if not is_admin and record.user_accounts != current_user.accounts:
        raise HTTPException(status_code=403, detail="无权查看此记录")

    return {
        "id": record.id,
        "error_type": record.error_type,
        "error_message": record.error_message,
        "traceback_summary": record.traceback_summary,
        "request_method": record.request_method,
        "request_path": record.request_path,
        "user_accounts": record.user_accounts,
        "user_real_name": record.user_real_name,
        "user_ip": record.user_ip,
        "request_query_params": record.request_query_params,
        "request_body_snippet": record.request_body_snippet,
        "analysis_status": record.analysis_status,
        "analysis_result": record.analysis_result,  # DeepSeek 的 Markdown 分析结果
        "analysis_error": record.analysis_error,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "analyzed_at": record.analyzed_at.isoformat() if record.analyzed_at else None,
    }


# =================================================================
#  DELETE /api/error-analyses/{analysis_id} — 删除单条
# =================================================================
@router.delete("/{analysis_id}", status_code=204)
def delete_analysis_record(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    删除一条错误分析记录
    - 普通用户只能删除自己的
    - 管理员/owner 可以删除任何人的
    """
    record = get_analysis(db, analysis_id)
    if not record:
        raise HTTPException(status_code=404, detail="分析记录不存在")

    # 权限检查
    is_admin = current_user.role in ("admin", "owner")
    if not is_admin and record.user_accounts != current_user.accounts:
        raise HTTPException(status_code=403, detail="无权删除此记录")

    success = delete_analysis(db, analysis_id)
    if not success:
        raise HTTPException(status_code=500, detail="删除失败")


# =================================================================
#  POST /api/error-analyses/clean — 手动清理旧记录（仅管理员）
# =================================================================
@router.post("/clean", status_code=200)
def clean_old_records(
    retention_days: int = Query(30, ge=1, le=365, description="保留天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    手动触发清理超过指定天数的旧分析记录（默认 30 天）
    仅管理员/owner 可用
    """
    if current_user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="权限不足")

    deleted_count = clean_old_analyses(db, retention_days=retention_days)
    return {
        "deleted_count": deleted_count,
        "retention_days": retention_days,
        "message": f"已清理 {deleted_count} 条超过 {retention_days} 天的旧记录",
    }
