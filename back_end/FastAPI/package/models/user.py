# models/user.py
from sqlalchemy import Column, Integer, String, Enum, DateTime, func
from ..database.database import Base


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
    # 创建时间，默认为当前时间
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    # 更新时间，每次更新记录自动更新时间
    updated_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now(), comment="更新时间")
    # 用户职位，可为空
    position = Column(String(50), nullable=True, comment="用户职位")
