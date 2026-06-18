# schemas/attachment.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .user import UserOut  # 复用用户响应模型


# 附件上传请求模型（前端上传时传递的参数）
class AttachmentCreate(BaseModel):
    """上传附件时的请求参数（实际文件通过multipart/form-data传递，此模型用于补充信息）"""
    # 注意：文件本身通过表单的file字段上传，这里无需定义file字段
    case_id: int = Field(..., description="关联的案件ID")
    uploaded_by: int = Field(..., description="上传人ID")

    class Config:
        from_attributes = True


# 附件响应模型（返回给前端的附件信息）
# 附件响应模型（返回给前端的附件信息）
class AttachmentOut(BaseModel):
    """附件详情响应模型，包含完整信息"""
    attachment_id: int = Field(..., description="附件ID")
    case_id: int = Field(..., description="关联的案件ID")
    file_name: str = Field(..., description="原始文件名（含扩展名）")
    file_path: Optional[str] = Field(None, description="文件存储相对路径（LOCAL 模式使用，仅供参考）")
    cos_key: Optional[str] = Field(None, description="COS 对象键（COS 模式使用）")
    file_size: int = Field(..., description="文件大小（字节）")
    file_type: Optional[str] = Field(None, description="文件MIME类型（如application/pdf）")
    preview_url: Optional[str] = Field(None, description="预览链接（由 storage_manager 动态计算）")
    download_url: Optional[str] = Field(None, description="下载链接（由 storage_manager 动态计算）")
    uploaded_by: int = Field(..., description="上传人ID")
    uploaded_at: datetime = Field(..., description="上传时间")
    uploader: Optional[UserOut] = Field(None, description="上传人信息（关联用户表）")

    class Config:
        from_attributes = True  # 支持从ORM对象转换


# 简化的附件列表响应模型（用于案件详情中展示附件列表，隐藏不必要字段）
class AttachmentSimpleOut(BaseModel):
    """简化的附件信息，用于列表展示"""
    attachment_id: int = Field(..., description="附件ID")
    file_name: str = Field(..., description="原始文件名")
    file_path: Optional[str] = Field(None, description="文件存储相对路径（仅供参考）")
    cos_key: Optional[str] = Field(None, description="COS 对象键")
    file_size: int = Field(..., description="文件大小（字节）")
    preview_url: Optional[str] = Field(None, description="预览链接")
    download_url: Optional[str] = Field(None, description="下载链接")
    uploaded_at: datetime = Field(..., description="上传时间")
    uploaded_by: int = Field(..., description="上传人ID")
    uploader: Optional[UserOut] = Field(None, description="上传人信息（关联用户表）")

    class Config:
        from_attributes = True