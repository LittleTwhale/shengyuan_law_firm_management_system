# models/party_building_model.py
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from ..database.database import Base


# 1. 党建分类模型
class PartyCategory(Base):
    __tablename__ = "party_categories"

    id = Column(Integer, primary_key=True, index=True, comment="分类ID")
    name = Column(String(100), nullable=False, comment="分类名称")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序权重(越大越靠前)")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")

    # ORM关系：关联该分类下的所有资料
    materials = relationship("PartyMaterial", back_populates="category")


# 2. 党建资料模型
class PartyMaterial(Base):
    __tablename__ = "party_materials"

    id = Column(Integer, primary_key=True, index=True, comment="资料ID")
    title = Column(String(255), nullable=False, index=True, comment="标题")

    # 新增需求字段
    issuing_authority = Column(String(100), nullable=True, comment="发文单位")
    document_number = Column(String(100), nullable=True, comment="文号")

    # 富文本内容 (使用 Text 或 LongText 存储 HTML)
    content = Column(Text, nullable=True, comment="主要内容(富文本HTML)")

    # 外键
    category_id = Column(Integer, ForeignKey("party_categories.id", ondelete="RESTRICT"), nullable=False,
                         comment="所属分类ID")
    publisher_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, comment="发布人ID")

    # 统计与时间
    view_count = Column(Integer, default=0, nullable=False, comment="阅读量")
    created_at = Column(DateTime, server_default=func.now(), comment="发布时间")
    updated_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now(), comment="更新时间")

    # ORM关系
    category = relationship("PartyCategory", back_populates="materials")
    publisher = relationship("User")  # 关联用户表，获取发布人姓名

    # 关联附件 (级联删除：删除资料时自动删除关联的附件记录)
    attachments = relationship("PartyAttachment", back_populates="material", cascade="all, delete-orphan")


# 3. 党建附件模型
class PartyAttachment(Base):
    __tablename__ = "party_attachments"

    id = Column(Integer, primary_key=True, index=True, comment="附件ID")

    material_id = Column(Integer, ForeignKey("party_materials.id", ondelete="CASCADE"), nullable=False,
                         comment="关联的资料ID")

    file_name = Column(String(255), nullable=False, comment="原文件名")
    file_path = Column(String(512), nullable=False, comment="文件存储路径")
    file_size = Column(Integer, nullable=False, comment="文件大小(字节)")
    file_type = Column(String(100), nullable=True, comment="文件MIME类型")
    cos_key = Column(String(512), nullable=True, comment="COS对象存储键（云存储模式）")

    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, comment="上传人ID")
    created_at = Column(DateTime, server_default=func.now(), comment="上传时间")

    # ORM关系
    material = relationship("PartyMaterial", back_populates="attachments")
    uploader = relationship("User")