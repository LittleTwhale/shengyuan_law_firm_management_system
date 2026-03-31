# models/system_announcement_model.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from ..database.database import Base

# 公告表
class SystemAnnouncement(Base):
    __tablename__ = "system_announcements"

    id = Column(Integer, primary_key=True, index=True, comment="公告ID")
    type = Column(String(50), nullable=False, index=True, comment="类型: update_log/general_notice")
    title = Column(String(255), nullable=False, comment="标题")
    version = Column(String(50), nullable=True, comment="关联版本号")

    content = Column(LONGTEXT, nullable=True, comment="公告内容(富文本HTML)")

    is_active = Column(Boolean, default=True, index=True, nullable=False, comment="是否发布")
    publisher_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, comment="发布人ID")

    created_at = Column(DateTime, server_default=func.now(), comment="发布时间")
    updated_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now(), comment="更新时间")

    # ORM关系
    publisher = relationship("User",foreign_keys="SystemAnnouncement.publisher_id")  # 关联用户表，用于获取发布人姓名

# 用户阅读记录表
class UserAnnouncementRead(Base):
    __tablename__ = "user_announcement_read"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    announcement_id = Column(Integer, ForeignKey("system_announcements.id", ondelete="CASCADE"), nullable=False, index=True, comment="公告ID")
    read_at = Column(DateTime, server_default=func.now(), comment="阅读时间")

    # 联合唯一索引：一个用户对一条公告只能有一条已读记录
    __table_args__ = (
        UniqueConstraint('user_id', 'announcement_id', name='uix_user_announcement_read'),
    )