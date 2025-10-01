# models/user.py
from sqlalchemy import Column, Integer, String, Enum, DateTime, func
from sqlalchemy.orm import relationship
from ..database.database import Base
from .case_operation import CaseOperation


# 定义用户模型，对应数据库中的 users 表
class User(Base):
    __tablename__ = "users"  # 数据库表名

    # 主键ID，自增
    id = Column(Integer, primary_key=True, index=True, comment="用户ID")

    # 用户账号，唯一且不能为空
    accounts = Column(String(50), unique=True, nullable=False, comment="用户登录账号")

    # 密码哈希存储，不能为空
    password_hash = Column(String(255), nullable=False, comment="密码哈希值")

    # 真实姓名，可为空
    real_name = Column(String(50), nullable=True, comment="用户真实姓名")

    # 用户角色，枚举类型：user 普通用户，admin 管理员，owner 所有者
    role = Column(Enum('user', 'admin', 'owner'), default='user', nullable=False, comment="用户角色")

    # 用户职位，可为空
    position = Column(String(50), nullable=True, comment="用户职位")

    # 创建时间，默认为当前时间
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    # 更新时间，每次更新记录自动更新时间
    updated_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now(), comment="更新时间")

    # ---------------- ORM 关系 ----------------
    # 用户提交的案件操作记录
    operations = relationship("CaseOperation", back_populates="user", foreign_keys=[CaseOperation.user_id])

    # 用户作为审核人的操作记录
    reviewed_operations = relationship("CaseOperation", back_populates="review_user", foreign_keys=[CaseOperation.review_user_id])

    # 用户作为主办律师的案件
    main_cases = relationship("Case", back_populates="main_lawyer", foreign_keys="Case.main_lawyer_id")

    # 用户作为助理律师的案件
    assistant_cases = relationship("Case", back_populates="assistant_lawyer", foreign_keys="Case.assistant_lawyer_id")

    # 用户作为执行主办律师的案件
    execution_cases = relationship("Case", back_populates="execution_lawyer", foreign_keys="Case.execution_lawyer_id")

    # 用户作为执行助理律师的案件
    execution_assistant_cases = relationship("Case", back_populates="execution_assistant", foreign_keys="Case.execution_assistant_id")
