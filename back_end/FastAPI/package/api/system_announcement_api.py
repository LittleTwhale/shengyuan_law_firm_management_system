# api/system_announcement_api.py
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..models.user import User
from ..api.deps import get_current_user
from ..schemas import system_announcement_schema as schemas
from ..crud import system_announcement_crud as crud

router = APIRouter(
    prefix="/system/announcements",
    tags=["System Announcements (系统公告)"]
)


# ---------------- 权限依赖 ----------------
def require_admin_access(current_user: User = Depends(get_current_user)):
    """
    检查用户是否有后台管理权限
    """
    if current_user.role in ['owner', 'admin']:
        return current_user

    perms = current_user.permissions or {}
    if perms.get("can_access_admin") is True:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="您没有系统后台管理权限"
    )


# ==========================================
# 用户端接口 (所有登录用户均可访问)
# ==========================================

@router.get("/unread", response_model=List[schemas.SystemAnnouncementOut])
def get_unread_announcements(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    获取当前用户所有生效且【未读】的公告。
    供前端登录后检查弹出，返回的是列表格式。
    """
    announcements = crud.get_unread_announcements(db, current_user.id)
    for ann in announcements:
        if ann.publisher:
            ann.publisher_name = ann.publisher.real_name
    return announcements


@router.post("/{announcement_id}/read")
def mark_as_read(
        announcement_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    用户阅读公告后调用此接口，将该条公告标记为已读
    """
    # 校验公告是否存在
    announcement = crud.get_announcement(db, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")

    crud.mark_announcement_as_read(db, current_user.id, announcement_id)
    return {"detail": "已标记为已读"}


@router.get("/unread/count")
def get_unread_announcement_count(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的未读公告数量（含全员公告和定向推送）
    供前端菜单角标使用
    """
    count = crud.count_unread_announcements(db, current_user.id)
    return {"count": count}


@router.get("/center/list", response_model=schemas.SystemAnnouncementUserPage)
def get_announcement_center(
        skip: int = 0,
        limit: int = 20,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    公告中心接口：分页获取对当前用户可见的所有公告（附带 is_read 状态）
    """
    total, items = crud.get_user_announcement_center_list(db, current_user.id, skip, limit)
    return {"total": total, "items": items}


# ==========================================
# 管理端接口 (需要管理员权限)
# ==========================================

@router.post("", response_model=schemas.SystemAnnouncementOut)
def create_announcement(
        obj_in: schemas.SystemAnnouncementCreate,
        db: Session = Depends(get_db),
        user: User = Depends(require_admin_access)
):
    """管理端：发布新公告"""
    announcement = crud.create_announcement(db, obj_in, publisher_id=user.id)
    return announcement


@router.get("", response_model=schemas.SystemAnnouncementPage)
def read_announcements(
        skip: int = 0,
        limit: int = 20,
        type: Optional[str] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        db: Session = Depends(get_db),
        user: User = Depends(require_admin_access)
):
    """管理端：获取全量公告列表（用于后台管理表格）"""
    total, items = crud.get_announcements(db, skip, limit, type, search, is_active)

    results = []
    for item in items:
        if item.publisher:
            item.publisher_name = item.publisher.real_name
        results.append(item)

    return {"total": total, "items": results}


@router.get("/{announcement_id}", response_model=schemas.SystemAnnouncementOut)
def read_announcement_detail(
        announcement_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(require_admin_access)
):
    """管理端：获取单条公告详情"""
    announcement = crud.get_announcement(db, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")

    if announcement.publisher:
        announcement.publisher_name = announcement.publisher.real_name

    return announcement


@router.put("/{announcement_id}", response_model=schemas.SystemAnnouncementOut)
def update_announcement(
        announcement_id: int,
        obj_in: schemas.SystemAnnouncementUpdate,
        db: Session = Depends(get_db),
        user: User = Depends(require_admin_access)
):
    """管理端：更新公告信息或状态"""
    announcement = crud.get_announcement(db, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")

    return crud.update_announcement(db, announcement, obj_in)


@router.delete("/{announcement_id}")
def delete_announcement(
        announcement_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(require_admin_access)
):
    """管理端：彻底删除公告"""
    success = crud.delete_announcement(db, announcement_id)
    if not success:
        raise HTTPException(status_code=404, detail="公告不存在")
    return {"detail": "删除成功"}

@router.get("/{announcement_id}/read_status", response_model=List[schemas.AnnouncementReadStatusOut])
def read_announcement_status(
        announcement_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(require_admin_access)
):
    """
    管理端：获取指定公告的全员阅读明细（已读/未读名单）
    """
    # 先检查公告是否存在
    announcement = crud.get_announcement(db, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")

    # 获取并返回阅读状态列表
    results = crud.get_announcement_read_status(db, announcement_id)
    return results