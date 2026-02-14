# schema/party_building_schema.py
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


# ----------------------
# 1. 分类相关的 Schema
# ----------------------
class PartyCategoryBase(BaseModel):
    name: str
    sort_order: Optional[int] = 0
    is_active: Optional[bool] = True


class PartyCategoryCreate(PartyCategoryBase):
    pass


class PartyCategoryUpdate(PartyCategoryBase):
    name: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class PartyCategoryOut(PartyCategoryBase):
    id: int

    class Config:
        from_attributes = True


# ----------------------
# 2. 附件相关的 Schema
# ----------------------
class PartyAttachmentOut(BaseModel):
    id: int
    file_name: str
    file_path: str
    file_size: int
    file_type: Optional[str] = None
    created_at: datetime
    # 这里只返回上传者名字，避免嵌套太深
    uploaded_by_name: Optional[str] = None

    class Config:
        from_attributes = True


# ----------------------
# 3. 资料（文章）相关的 Schema
# ----------------------
class PartyMaterialBase(BaseModel):
    title: str
    issuing_authority: Optional[str] = None  # 发文单位
    document_number: Optional[str] = None  # 文号
    content: Optional[str] = None  # 富文本内容
    category_id: int


class PartyMaterialCreate(PartyMaterialBase):
    pass


class PartyMaterialUpdate(BaseModel):
    title: Optional[str] = None
    issuing_authority: Optional[str] = None
    document_number: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[int] = None


class PartyMaterialOut(PartyMaterialBase):
    id: int
    view_count: int
    created_at: datetime
    updated_at: datetime
    publisher_id: int

    # 嵌套返回关联对象
    category: Optional[PartyCategoryOut] = None
    attachments: List[PartyAttachmentOut] = []

    # 额外字段：发布人姓名（通过API层处理或ORM @property获取）
    publisher_name: Optional[str] = None

    class Config:
        from_attributes = True

# 分页响应 Schema ===
class PartyMaterialPage(BaseModel):
    total: int
    items: List[PartyMaterialOut]