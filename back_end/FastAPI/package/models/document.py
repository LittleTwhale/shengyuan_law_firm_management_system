# models/document.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from ..database.database import Base


class DocumentTemplate(Base):
    __tablename__ = "document_templates" 

    # 字段定义（与表结构一一对应）
    id = Column(Integer, primary_key=True, index=True, comment="模板ID")
    name = Column(String(255), nullable=False, comment="模板名称（")
    file_path = Column(String(512), nullable=False, comment="模板文件存储路径")
    file_type = Column(String(100), nullable=False, comment="文件类型（如：application/docx）")
    file_size = Column(Integer, nullable=False, comment="文件大小（单位：KB）")
    description = Column(Text, nullable=True, comment="模板描述（可选）")
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, comment="上传人ID")
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="上传时间")
    updated_at = Column(TIMESTAMP, server_default=func.now(), server_onupdate=func.now(), comment="更新时间")

    # ORM关系：关联用户表（上传人信息）
    uploader = relationship("User", backref="uploaded_templates")  # 一个用户可上传多个模板