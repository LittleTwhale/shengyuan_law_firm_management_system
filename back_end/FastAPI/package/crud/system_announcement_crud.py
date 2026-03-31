# crud/system_announcement_crud.py
from typing import Optional, Tuple, List
from sqlalchemy import desc, and_
from sqlalchemy.orm import Session, joinedload

from ..models.system_announcement_model import SystemAnnouncement, UserAnnouncementRead
from ..schemas.system_announcement_schema import SystemAnnouncementCreate, SystemAnnouncementUpdate


# ==========================================
# 管理端基础操作
# ==========================================
# 获取指定ID的公告
def get_announcement(db: Session, announcement_id: int) -> Optional[SystemAnnouncement]:
    return db.query(SystemAnnouncement) \
        .options(joinedload(SystemAnnouncement.publisher)) \
        .filter(SystemAnnouncement.id == announcement_id) \
        .first()

# 获取公告列表
def get_announcements(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        announce_type: Optional[str] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
) -> Tuple[int, List[SystemAnnouncement]]:
    query = db.query(SystemAnnouncement)

    if announce_type:
        query = query.filter(SystemAnnouncement.type == announce_type)

    if is_active is not None:
        query = query.filter(SystemAnnouncement.is_active == is_active)

    if search:
        query = query.filter(
            (SystemAnnouncement.title.ilike(f"%{search}%")) |
            (SystemAnnouncement.version.ilike(f"%{search}%"))
        )

    total = query.count()
    items = query.options(joinedload(SystemAnnouncement.publisher)) \
        .order_by(desc(SystemAnnouncement.created_at)) \
        .offset(skip).limit(limit).all()

    return total, items

# 创建公告
def create_announcement(db: Session, obj_in: SystemAnnouncementCreate, publisher_id: int) -> SystemAnnouncement:
    db_obj = SystemAnnouncement(
        type=obj_in.type,
        title=obj_in.title,
        version=obj_in.version,
        content=obj_in.content,
        is_active=obj_in.is_active,
        publisher_id=publisher_id
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

# 更新公告
def update_announcement(db: Session, db_obj: SystemAnnouncement,
                        obj_in: SystemAnnouncementUpdate) -> SystemAnnouncement:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

# 删除公告
def delete_announcement(db: Session, announcement_id: int) -> bool:
    db_obj = db.query(SystemAnnouncement).filter(SystemAnnouncement.id == announcement_id).first()
    if not db_obj:
        return False
    db.delete(db_obj)
    db.commit()
    return True


# ==========================================
# 用户端扩展操作 (已读状态、未读列表、公告中心)
# ==========================================

def get_unread_announcements(db: Session, user_id: int) -> List[SystemAnnouncement]:
    """获取指定用户所有生效中且尚未阅读的公告"""
    # 左连接 UserAnnouncementRead，过滤出没有匹配记录的数据（即未读）
    unread_announcements = db.query(SystemAnnouncement).outerjoin(
        UserAnnouncementRead,
        and_(
            SystemAnnouncement.id == UserAnnouncementRead.announcement_id,
            UserAnnouncementRead.user_id == user_id
        )
    ).options(joinedload(SystemAnnouncement.publisher)).filter(
        SystemAnnouncement.is_active == True,
        UserAnnouncementRead.id == None  # 核心：没有阅读记录
    ).order_by(desc(SystemAnnouncement.created_at)).all()

    return unread_announcements


def get_user_announcement_center_list(
        db: Session, user_id: int, skip: int = 0, limit: int = 20
) -> Tuple[int, List[dict]]:
    """获取用户视角的公告中心列表，附带是否已读的状态"""
    # 联合查询主表和已读记录表的时间
    query = db.query(SystemAnnouncement, UserAnnouncementRead.read_at).outerjoin(
        UserAnnouncementRead,
        and_(
            SystemAnnouncement.id == UserAnnouncementRead.announcement_id,
            UserAnnouncementRead.user_id == user_id
        )
    ).filter(SystemAnnouncement.is_active == True)  # 普通用户只能看到处于发布状态的公告

    total = query.count()
    results = query.options(joinedload(SystemAnnouncement.publisher)) \
        .order_by(desc(SystemAnnouncement.created_at)) \
        .offset(skip).limit(limit).all()

    # 将元组 (SystemAnnouncement, read_at) 转化为前端需要的字典格式
    formatted_items = []
    for announcement, read_at in results:
        # 将 SQLAlchemy 对象转为字典
        ann_dict = {c.name: getattr(announcement, c.name) for c in announcement.__table__.columns}
        # 补充关联关系和自定义字段
        ann_dict['publisher_name'] = announcement.publisher.real_name if announcement.publisher else None
        ann_dict['is_read'] = bool(read_at)
        ann_dict['read_at'] = read_at
        formatted_items.append(ann_dict)

    return total, formatted_items


def mark_announcement_as_read(db: Session, user_id: int, announcement_id: int) -> bool:
    """将某条公告标记为已读"""
    # 检查是否已经标记过，避免重复写入触发数据库联合唯一约束报错
    existing = db.query(UserAnnouncementRead).filter(
        UserAnnouncementRead.user_id == user_id,
        UserAnnouncementRead.announcement_id == announcement_id
    ).first()

    if not existing:
        new_read = UserAnnouncementRead(user_id=user_id, announcement_id=announcement_id)
        db.add(new_read)
        db.commit()
    return True