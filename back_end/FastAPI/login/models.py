# models.py
from sqlalchemy import Column, Integer, String, Enum, DateTime, func
from .database import Base
import enum

# 定义枚举类与 MySQL ENUM 对应
class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"
    owner = "owner"

class User(Base):
    """
    对应 MySQL 中已存在的 users 表
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    accounts = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    real_name = Column(String(50))
    role = Column(Enum(UserRole), default=UserRole.user)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp())

