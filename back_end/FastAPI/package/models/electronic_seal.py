# models/electronic_seal.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from ..database.database import Base


class ElectronicSeal(Base):
    """电子印章模型，对应 electronic_seals 表"""
    __tablename__ = "electronic_seals"

    id = Column(Integer, primary_key=True, index=True, comment="印章ID（主键）")
    name = Column(String(100), nullable=False, comment="印章名称（如“公章”“合同章”）")
    image_path = Column(String(512), nullable=False, comment="印章图片存储路径")
    image_type = Column(String(50), nullable=False, comment="图片类型（如image/png）")
    image_size = Column(Integer, nullable=False, comment="图片大小（单位：KB）")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否启用")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now(), comment="更新时间")

    # ORM关系：关联用印申请（一个印章可被多个申请使用）
    seal_applications = relationship("SealApplication", back_populates="seal")


class SealApplication(Base):
    """用印申请模型，对应 seal_applications 表"""
    __tablename__ = "seal_applications"

    id = Column(Integer, primary_key=True, index=True, comment="申请ID（主键）")
    applicant_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="申请人ID（关联用户表）")
    file_name = Column(String(255), nullable=False, comment="申请盖章的文件名")
    file_path = Column(String(512), nullable=False, comment="文件存储路径")
    file_type = Column(String(50), nullable=False, comment="文件类型（如application/pdf）")
    file_size = Column(Integer, nullable=False, comment="文件大小（单位：KB）")
    seal_id = Column(Integer, ForeignKey("electronic_seals.id"), nullable=False, comment="申请使用的印章ID")
    application_reason = Column(Text, nullable=True, comment="用印原因（可选）")
    status = Column(String(20), nullable=False, default="待审核", comment="申请状态（待审核/已通过/已拒绝）")
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="审核人ID")
    review_time = Column(DateTime, nullable=True, comment="审核时间")
    review_remark = Column(Text, nullable=True, comment="审核备注（可选）")
    sealed_file_path = Column(String(512), nullable=True, comment="盖章后的文件存储路径")
    created_at = Column(DateTime, server_default=func.now(), comment="申请时间")
    updated_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now(), comment="更新时间")

    # ORM关系
    applicant = relationship("User", foreign_keys="[SealApplication.applicant_id]", backref="submitted_seal_applications")  # 申请人
    reviewer = relationship("User", foreign_keys="[SealApplication.reviewer_id]", backref="reviewed_seal_applications")  # 审核人

    seal = relationship("ElectronicSeal", back_populates="seal_applications")  # 关联的印章
    seal_positions = relationship("SealPosition", back_populates="application", cascade="all, delete-orphan")  # 印章位置配置


class SealPosition(Base):
    """印章位置配置模型，对应 seal_positions 表"""
    __tablename__ = "seal_positions"

    id = Column(Integer, primary_key=True, index=True, comment="配置ID（主键）")
    application_id = Column(Integer, ForeignKey("seal_applications.id", ondelete="CASCADE"), nullable=False, comment="关联的用印申请ID")
    page_num = Column(Integer, nullable=False, comment="印章所在页码（从1开始）")
    x = Column(Float, nullable=False, comment="印章左上角X坐标（px）")
    y = Column(Float, nullable=False, comment="印章左上角Y坐标（px）")
    width = Column(Float, nullable=False, comment="印章宽度（px）")
    height = Column(Float, nullable=False, comment="印章高度（px）")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    # ORM关系：关联用印申请（一个申请可配置多个印章位置）
    application = relationship("SealApplication", back_populates="seal_positions")