# models/attachment.py
from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from ..database.database import Base


class CaseAttachment(Base):
    __tablename__ = "case_attachments"  # 对应数据库表名

    # 字段定义（与表结构一致）
    attachment_id = Column(Integer, primary_key=True, index=True, comment="附件ID，自增主键")
    case_id = Column(Integer, ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False, comment="关联的案件ID")
    file_name = Column(String(255), nullable=False, comment="附件原始文件名（含扩展名）")
    file_path = Column(String(512), nullable=False, comment="附件存储的相对路径")
    file_size = Column(Integer, nullable=False, comment="附件大小（单位：字节）")
    file_type = Column(String(100), comment="文件MIME类型（如application/pdf）")
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, comment="上传人ID")
    uploaded_at = Column(TIMESTAMP, server_default=func.now(), comment="上传时间")

    # ORM关系：关联案件表和用户表
    case = relationship("Case", backref="attachments")  # 一个案件可关联多个附件
    uploader = relationship("User", backref="uploaded_attachments")  # 一个用户可上传多个附件