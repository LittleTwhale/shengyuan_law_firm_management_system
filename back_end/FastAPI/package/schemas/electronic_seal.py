# models/electronic_seal.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .user import UserOut


# 电子印章创建请求模型
class ElectronicSealCreate(BaseModel):
    name: str = Field(..., description="印章名称（如“公章”“合同章”）")
    # 注意：图片文件通过multipart/form-data上传，此处无需定义file字段
    # 前端传递文件时，额外参数通过该模型传递

    class Config:
        from_attributes = True


# 电子印章更新请求模型（仅更新可修改字段）
class ElectronicSealUpdate(BaseModel):
    name: Optional[str] = Field(None, description="印章名称")
    is_active: Optional[bool] = Field(None, description="是否启用")

    class Config:
        from_attributes = True


# 电子印章响应模型（完整信息）
class ElectronicSealOut(BaseModel):
    id: int = Field(..., description="印章ID")
    name: str = Field(..., description="印章名称")
    image_path: str = Field(..., description="印章图片存储路径（后端内部使用）")
    image_type: str = Field(..., description="图片类型（如image/png）")
    image_size: int = Field(..., description="图片大小（KB）")
    is_active: bool = Field(..., description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 用印申请创建请求模型
class SealApplicationCreate(BaseModel):
    file_name: str = Field(..., description="申请盖章的文件名")
    seal_id: int = Field(..., description="申请使用的印章ID")
    application_reason: Optional[str] = Field(None, description="用印原因（可选）")
    # 注意：待盖章文件通过multipart/form-data上传，此处无需定义file字段

    class Config:
        from_attributes = True


# 用印申请审核请求模型
class SealApplicationReview(BaseModel):
    status: str = Field(..., description="审核结果（已通过/已拒绝）")
    review_remark: Optional[str] = Field(None, description="审核备注（可选）")

    class Config:
        from_attributes = True


# 印章位置配置模型（用于创建/返回位置信息）
class SealPositionBase(BaseModel):
    page_num: int = Field(..., description="印章所在页码（从1开始）")
    x: float = Field(..., description="印章左上角X坐标（px）")
    y: float = Field(..., description="印章左上角Y坐标（px）")
    width: float = Field(..., description="印章宽度（px）")
    height: float = Field(..., description="印章高度（px）")

    class Config:
        from_attributes = True


# 用印申请响应模型（完整信息）
class SealApplicationOut(BaseModel):
    id: int = Field(..., description="申请ID")
    applicant_id: int = Field(..., description="申请人ID")
    applicant: Optional[UserOut] = Field(None, description="申请人信息")
    file_name: str = Field(..., description="申请盖章的文件名")
    file_path: str = Field(..., description="文件存储路径（后端内部使用）")
    file_type: str = Field(..., description="文件类型（如application/pdf）")
    file_size: int = Field(..., description="文件大小（KB）")
    seal_id: int = Field(..., description="申请使用的印章ID")
    seal: Optional[ElectronicSealOut] = Field(None, description="印章信息")
    application_reason: Optional[str] = Field(None, description="用印原因")
    status: str = Field(..., description="申请状态（待审核/已通过/已拒绝）")
    reviewer_id: Optional[int] = Field(None, description="审核人ID")
    reviewer: Optional[UserOut] = Field(None, description="审核人信息")
    review_time: Optional[datetime] = Field(None, description="审核时间")
    review_remark: Optional[str] = Field(None, description="审核备注")
    sealed_file_path: Optional[str] = Field(None, description="盖章后的文件路径")
    seal_positions: Optional[List[SealPositionBase]] = Field(None, description="印章位置配置")
    created_at: datetime = Field(..., description="申请时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 简化的用印申请列表模型（用于列表展示）
class SealApplicationSimpleOut(BaseModel):
    id: int = Field(..., description="申请ID")
    file_name: str = Field(..., description="文件名")
    seal: Optional[ElectronicSealOut] = Field(None, description="印章信息")
    status: str = Field(..., description="申请状态")
    applicant: Optional[UserOut] = Field(None, description="申请人")
    created_at: datetime = Field(..., description="申请时间")

    class Config:
        from_attributes = True