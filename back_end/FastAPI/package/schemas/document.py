# schemas/document.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .user import UserOut


# 模板上传请求模型（仅包含前端需要传递的参数）
class TemplateCreate(BaseModel):
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    uploaded_by: int = Field(..., description="上传人ID")

    class Config:
        from_attributes = True


# 模板响应模型（返回给前端的完整信息）
class TemplateOut(BaseModel):
    id: int = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    file_path: str = Field(..., description="文件存储路径（后端内部使用）")
    file_type: str = Field(..., description="文件MIME类型")
    file_size: int = Field(..., description="文件大小（KB）")
    description: Optional[str] = Field(None, description="模板描述")
    uploaded_by: int = Field(..., description="上传人ID")
    uploader: Optional[UserOut] = Field(None, description="上传人信息")
    created_at: datetime = Field(..., description="上传时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True  # 支持从ORM对象转换