# schemas/system_announcement_schema.py
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


# ----------------------
# 系统公告/更新日志 Schema
# ----------------------
class SystemAnnouncementBase(BaseModel):
    type: str  # update_log 或 general_notice
    title: str
    version: Optional[str] = None
    content: Optional[str] = None
    is_active: Optional[bool] = True

# 创建
class SystemAnnouncementCreate(SystemAnnouncementBase):
    pass

# 更新
class SystemAnnouncementUpdate(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    version: Optional[str] = None
    content: Optional[str] = None
    is_active: Optional[bool] = None

# 公告显示
class SystemAnnouncementOut(SystemAnnouncementBase):
    id: int
    publisher_id: int
    created_at: datetime
    updated_at: datetime
    publisher_name: Optional[str] = None

    class Config:
        from_attributes = True

# 公告分页
class SystemAnnouncementPage(BaseModel):
    total: int
    items: List[SystemAnnouncementOut]

# 专门给普通用户查看的结构（包含已读状态）
class SystemAnnouncementUserOut(SystemAnnouncementOut):
    is_read: bool = False
    read_at: Optional[datetime] = None

# 普通用户公告分页
class SystemAnnouncementUserPage(BaseModel):
    total: int
    items: List[SystemAnnouncementUserOut]

# 公告已读状态
class AnnouncementReadStatusOut(BaseModel):
    user_id: int
    real_name: Optional[str] = None
    role: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True