# schemas/electronic_seal.py
from pydantic import BaseModel, Field
from typing import Optional, List, Generic, TypeVar
from datetime import datetime
from .user import UserOut

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """通用分页响应"""
    items: List[T]
    total: int
    page: int
    page_size: int


# ----------------------
# 电子印章相关 Schemas
# ----------------------

class ElectronicSealCreate(BaseModel):
    """创建印章请求参数 (文件通过 multipart/form-data 上传)"""
    name: str = Field(..., description="印章名称")


class ElectronicSealUpdate(BaseModel):
    """更新印章状态"""
    is_active: bool = Field(..., description="是否启用")


class ElectronicSealOut(BaseModel):
    """印章信息响应"""
    id: int
    name: str
    image_path: str
    file_size: int
    is_active: bool
    uploaded_by: int
    uploader: Optional[UserOut] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ----------------------
# 用印申请相关 Schemas
# ----------------------

class SealApplicationCreate(BaseModel):
    """提交用印申请参数 (文件通过 multipart/form-data 上传)"""
    seal_id: int = Field(..., description="使用的印章ID")
    apply_reason: Optional[str] = Field(None, description="用印原因")


class SealApplicationReview(BaseModel):
    """审核操作请求"""
    status: str = Field(..., pattern="^(已通过|已拒绝)$", description="审核结果")
    review_remark: Optional[str] = Field(None, description="审核备注/拒绝原因")


# 盖章位置日志模型 (作为 confirm 接口的参数之一)
class SealLocationLog(BaseModel):
    page_number: int
    x: float
    y: float
    width: float
    height: float


class SealApplicationConfirm(BaseModel):
    """确认盖章完成请求 (仅用于结构描述，实际通过 Form Data 传递)"""
    # 注意：stamped_file 文件流单独传
    # logs 将作为 JSON 字符串传递
    pass


class SealAuditLogOut(BaseModel):
    """审计日志响应"""
    page_number: int
    x_coordinate: float
    y_coordinate: float
    created_at: datetime

    class Config:
        from_attributes = True


class SealApplicationOut(BaseModel):
    """用印申请完整详情响应"""
    id: int
    applicant_id: int
    applicant: Optional[UserOut]
    seal_id: int
    seal: Optional[ElectronicSealOut]

    original_file_name: str
    file_type: str
    # 仅返回预览PDF路径给前端，原文件路径一般不暴露或按需暴露
    preview_pdf_path: Optional[str]
    stamped_file_path: Optional[str]

    apply_reason: Optional[str]
    status: str

    reviewer: Optional[UserOut]
    review_time: Optional[datetime]
    review_remark: Optional[str]

    created_at: datetime
    updated_at: datetime

    # 包含审计日志
    audit_logs: List[SealAuditLogOut] = []

    class Config:
        from_attributes = True


# 列表页使用的简化模型
class SealApplicationSimpleOut(BaseModel):
    id: int
    original_file_name: str
    applicant: Optional[UserOut]
    seal: Optional[ElectronicSealOut]
    status: str
    stamped_file_path: Optional[str]
    preview_pdf_path: Optional[str] = None  # 用于前端判断 Word 转换是否完成

    apply_reason: Optional[str]
    review_remark: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True