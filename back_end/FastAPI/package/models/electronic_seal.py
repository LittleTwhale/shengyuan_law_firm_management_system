# models/electronic_seal.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey, Float, Text, Enum
from sqlalchemy.orm import relationship
from ..database.database import Base


class ElectronicSeal(Base):
    """电子印章模型"""
    __tablename__ = "electronic_seals"

    id = Column(Integer, primary_key=True, index=True, comment="印章ID")
    name = Column(String(100), nullable=False, comment="印章名称")
    image_path = Column(String(512), nullable=False, comment="印章图片路径")
    file_size = Column(Integer, default=0, comment="文件大小(KB)")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="上传人ID")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now(), comment="更新时间")

    # 关系
    uploader = relationship("User", foreign_keys=lambda: [ElectronicSeal.uploaded_by], backref="uploaded_seals")
    applications = relationship("SealApplication", back_populates="seal")


class SealApplication(Base):
    """用印申请模型"""
    __tablename__ = "seal_applications"

    id = Column(Integer, primary_key=True, index=True, comment="申请ID")
    applicant_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="申请人ID")
    seal_id = Column(Integer, ForeignKey("electronic_seals.id"), nullable=False, comment="印章ID")

    # 原始文件信息
    original_file_name = Column(String(255), nullable=False, comment="原始文件名")
    original_file_path = Column(String(512), nullable=False, comment="原始文件路径（可能是Word或PDF）")
    file_type = Column(String(200), nullable=False, comment="原始文件类型")

    # 预览/底图文件 (Word转PDF后的路径，或者是原PDF路径)
    preview_pdf_path = Column(String(512), nullable=True, comment="预览/盖章底图PDF路径")

    # 申请详情
    apply_reason = Column(Text, nullable=True, comment="用印原因")
    status = Column(Enum('待审核', '已通过', '已拒绝'), default='待审核', nullable=False, comment="申请状态")

    # 审核信息
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="审核人ID")
    review_time = Column(DateTime, nullable=True, comment="审核时间")
    review_remark = Column(Text, nullable=True, comment="审核备注")

    # 结果文件 (前端合成后回传的PDF)
    stamped_file_path = Column(String(512), nullable=True, comment="已盖章文件路径")

    created_at = Column(DateTime, server_default=func.now(), comment="申请时间")
    updated_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now(), comment="更新时间")

    # 关系
    applicant = relationship("User", foreign_keys=lambda: [SealApplication.applicant_id], backref="my_seal_applications")
    reviewer = relationship("User", foreign_keys=lambda: [SealApplication.reviewer_id], backref="reviewed_seal_applications")
    seal = relationship("ElectronicSeal", back_populates="applications")
    audit_logs = relationship("SealAuditLog", back_populates="application", cascade="all, delete-orphan")


class SealAuditLog(Base):
    """盖章操作审计日志 (记录盖章坐标)"""
    __tablename__ = "seal_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("seal_applications.id", ondelete="CASCADE"), nullable=False)

    # 坐标位置信息 (前端传回)
    page_number = Column(Integer, nullable=False, comment="页码")
    x_coordinate = Column(Float, nullable=False, comment="X坐标")
    y_coordinate = Column(Float, nullable=False, comment="Y坐标")
    seal_width = Column(Float, nullable=False, comment="印章宽度")
    seal_height = Column(Float, nullable=False, comment="印章高度")

    created_at = Column(DateTime, server_default=func.now())

    # 关系
    application = relationship("SealApplication", back_populates="audit_logs")