# schemas/electronic_volume_schema.py
from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator
from .user import UserOut


# ---------------------------------------------------------
# 辅助 Schemas (引用案件信息)
# ---------------------------------------------------------

class CaseSimpleInfo(BaseModel):
    """简化案件基础信息 (用于列表展示)"""
    case_number: Optional[str] = None
    case_category: Optional[str] = None
    main_lawyer: Optional[UserOut] = None

    class Config:
        from_attributes = True


class VolumeFilterQuery(BaseModel):
    """卷宗列表/统计 筛选参数"""
    keyword: Optional[str] = None  # 搜索 案号/委托人/卷宗名
    start_date: Optional[date] = None  # 按案件委托时间筛选
    end_date: Optional[date] = None
    lawyer_id: Optional[int] = None  # 筛选主办律师
    case_category: Optional[str] = None  # 筛选案件类型
    sort_by: Optional[str] = 'updated_at'  # 排序字段: created_at, updated_at
    sort_order: Optional[str] = 'desc'  # 排序方向: asc, desc


# ---------------------------------------------------------
# 卷内文件 (VolumeFile) Schemas
# ---------------------------------------------------------

class VolumeFileBase(BaseModel):
    file_name: str = Field(..., description="文件显示名称")
    category: str = Field("其他材料", description="文件目录分类")
    sort_order: Optional[int] = Field(0, description="排序权重")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    summary: Optional[str] = Field(None, description="摘要/备注")
    page_start: Optional[int] = Field(None, description="起始页码")
    page_end: Optional[int] = Field(None, description="结束页码")


class VolumeFileCreate(VolumeFileBase):
    volume_id: int = Field(..., description="所属卷宗ID")
    file_path: str = Field(..., description="文件存储路径")
    file_size: int = Field(..., description="文件大小(字节)")
    file_type: Optional[str] = Field(None, description="文件MIME类型")
    ocr_content: Optional[str] = Field(None, description="OCR识别文本")

    # 允许前端传 JSON 字符串或列表，自动处理 tags
    @field_validator('tags', mode='before')
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except:
                return []
        return v


class VolumeFileUpdate(BaseModel):
    file_name: Optional[str] = None
    category: Optional[str] = None
    sort_order: Optional[int] = None
    tags: Optional[List[str]] = None
    summary: Optional[str] = None
    ocr_content: Optional[str] = None
    ocr_status: Optional[str] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None

class SortItem(BaseModel):
    id: int
    sort_order: int


class VolumeFileOut(VolumeFileBase):
    id: int
    volume_id: int
    file_path: str
    file_size: int
    file_type: Optional[str]
    uploaded_by: Optional[int]
    created_at: datetime
    ocr_content: Optional[str] = None
    ocr_status: Optional[str] = 'pending'

    # 用于前端展示上传者名称（需要在 CRUD 层 join 或 再次查询，或者前端根据 ID 匹配）
    uploader_name: Optional[str] = None

    # 云存储支持
    cos_key: Optional[str] = None
    preview_url: Optional[str] = None
    download_url: Optional[str] = None

    class Config:
        from_attributes = True


class VolumeFileBriefOut(VolumeFileBase):
    """
    文件简要信息（不含 OCR 全文），用于卷宗详情初始加载，
    避免 OCR 大字段拖慢首次响应速度。
    """
    id: int
    volume_id: int
    file_path: str
    file_size: int
    file_type: Optional[str]
    uploaded_by: Optional[int]
    created_at: datetime
    ocr_status: Optional[str] = 'pending'
    uploader_name: Optional[str] = None

    # 云存储支持
    cos_key: Optional[str] = None
    preview_url: Optional[str] = None
    download_url: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------
# 案件卷宗 (CaseVolume) Schemas
# ---------------------------------------------------------

class CaseVolumeBase(BaseModel):
    name: str = Field(..., description="案卷名称")
    sort_order: Optional[int] = Field(0, description="显示排序")
    physical_location: Optional[str] = Field(None, description="纸质原件存放位置")


class CaseVolumeCreate(CaseVolumeBase):
    case_id: Optional[int] = Field(None, description="关联案件ID（独立卷宗时不传）")
    # 独立卷宗扩展字段
    client_name: Optional[str] = Field(None, description="委托人姓名")
    client_phone: Optional[str] = Field(None, description="委托人电话")
    main_lawyer_name: Optional[str] = Field(None, description="主办律师")
    case_description: Optional[str] = Field(None, description="案件简要描述")
    category: Optional[str] = Field(None, description="案件类别")


class CaseVolumeUpdate(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None
    physical_location: Optional[str] = None
    merged_file_path: Optional[str] = None  # 允许单独更新合并后的文件路径
    # 独立卷宗扩展字段
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    main_lawyer_name: Optional[str] = None
    case_description: Optional[str] = None
    category: Optional[str] = None


class CaseVolumeOut(CaseVolumeBase):
    id: int
    case_id: Optional[int] = None
    merged_file_path: Optional[str]
    created_at: datetime
    updated_at: datetime

    # 独立卷宗扩展字段
    is_standalone: Optional[int] = 0
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    main_lawyer_name: Optional[str] = None
    case_description: Optional[str] = None
    category: Optional[str] = None
    created_by: Optional[int] = None
    creator_name: Optional[str] = None

    # 包含卷内文件列表（含 OCR 全文）
    files: List[VolumeFileOut] = []

    # 包含案件简要信息 (用于列表显示，独立卷宗时为 None)
    case: Optional[CaseSimpleInfo] = None

    # 云存储支持
    cos_key: Optional[str] = None
    preview_url: Optional[str] = None
    download_url: Optional[str] = None

    class Config:
        from_attributes = True


class CaseVolumeDetailOut(CaseVolumeBase):
    """
    卷宗详情专用 Schema（文件列表不含 OCR 全文），
    用于详情页初始加载，减轻网络传输压力。
    """
    id: int
    case_id: Optional[int] = None
    merged_file_path: Optional[str]
    created_at: datetime
    updated_at: datetime

    # 独立卷宗扩展字段
    is_standalone: Optional[int] = 0
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    main_lawyer_name: Optional[str] = None
    case_description: Optional[str] = None
    category: Optional[str] = None
    created_by: Optional[int] = None
    creator_name: Optional[str] = None

    # 文件列表（不含 OCR 全文）
    files: List[VolumeFileBriefOut] = []

    # 包含案件简要信息
    case: Optional[CaseSimpleInfo] = None

    # 云存储支持
    cos_key: Optional[str] = None
    preview_url: Optional[str] = None
    download_url: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------
# 搜索与聚合 Schemas
# ---------------------------------------------------------

class VolumeSimpleOut(BaseModel):
    """仅包含卷宗基本信息，不含文件列表（用于下拉列表等）"""
    id: int
    name: str
    case_id: int

    class Config:
        from_attributes = True


class CaseVolumeListOut(CaseVolumeBase):
    """
    卷宗列表专用 Schema（不包含 files 列表，避免 Ocr 全文数据拖慢列表加载）
    替代 CaseVolumeOut 用于列表场景
    """
    id: int
    case_id: Optional[int] = None
    merged_file_path: Optional[str]
    created_at: datetime
    updated_at: datetime

    # 独立卷宗扩展字段
    is_standalone: Optional[int] = 0
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    main_lawyer_name: Optional[str] = None
    case_description: Optional[str] = None
    category: Optional[str] = None
    created_by: Optional[int] = None
    creator_name: Optional[str] = None

    # 文件数量（通过子查询预加载，避免 N+1）
    file_count: int = 0

    # 案件概要（独立卷宗时为 None）
    case: Optional[CaseSimpleInfo] = None

    # 云存储支持
    cos_key: Optional[str] = None
    preview_url: Optional[str] = None
    download_url: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------
# 分页响应模型 (Pagination Schemas)
# ---------------------------------------------------------

class CaseVolumePageOut(BaseModel):
    """卷宗列表分页模型（完整信息，含文件列表）"""
    total: int
    merged_count: int = 0
    items: List[CaseVolumeOut]


class CaseVolumePageListOut(BaseModel):
    """卷宗列表分页模型（轻量，不含文件列表和OCR全文）"""
    total: int
    merged_count: int = 0
    items: List[CaseVolumeListOut]


class VolumeFilePageOut(BaseModel):
    """卷内文件列表分页模型"""
    total: int
    items: List[VolumeFileOut]