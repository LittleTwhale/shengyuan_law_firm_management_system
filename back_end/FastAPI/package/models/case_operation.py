# models/case_operation.py
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, JSON, func
from ..database.database import Base
from sqlalchemy.orm import relationship
from .case import Case


class CaseOperation(Base):
    __tablename__ = "case_operations"  # 数据库表名

    # 主键ID
    operation_id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="操作ID")

    # 关联案件ID（可为空）
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=True, comment="关联案件ID")

    # 操作用户ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="操作用户ID")

    # 操作类型：新增、修改、删除
    operation_type = Column(Enum("新增", "修改", "删除"), nullable=False, comment="操作类型")

    # 待审核的数据（JSON 格式存储）
    pending_data = Column(JSON, nullable=True, comment="待审核的数据")

    # 审核状态
    review_status = Column(Enum("待审核", "已通过", "已拒绝"), default="待审核", nullable=False, comment="审核状态")

    # 审核人 ID
    review_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="审核人ID")

    # 审核备注
    review_remark = Column(String(255), nullable=True, comment="审核备注")

    # 审核时间
    reviewed_at = Column(DateTime, nullable=True, comment="审核时间")

    # 创建 & 更新时间
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now(), comment="更新时间")

    # ORM 关系
    case = relationship(Case, back_populates="operations", foreign_keys="CaseOperation.case_id")
    user = relationship("User", back_populates="operations", foreign_keys="CaseOperation.user_id")
    review_user = relationship("User", back_populates="reviewed_operations", foreign_keys="CaseOperation.review_user_id")
