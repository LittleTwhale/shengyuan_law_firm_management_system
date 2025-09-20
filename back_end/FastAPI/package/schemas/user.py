# schemas/user.py
from pydantic import BaseModel, Field, constr
from typing import Optional
from datetime import datetime

# 用户基础信息模型
class UserBase(BaseModel):
    accounts: constr(min_length=3, max_length=50) = Field(..., description="用户账号")
    real_name: Optional[str] = Field(None, description="真实姓名")
    role: Optional[str] = Field("user", description="用户角色，可选值: user/admin/owner")

# 创建用户模型（含密码）
class UserCreate(UserBase):
    password: constr(min_length=6, max_length=20) = Field(..., description="用户密码")

# 用户响应模型（返回给前端，不包含密码）
class UserOut(UserBase):
    id: int = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True  # 告诉 Pydantic 可以读取 ORM 对象

# 登录请求模型
class UserLogin(BaseModel):
    accounts: str = Field(..., description="用户账号")
    password: str = Field(..., description="用户密码")

# Token 响应模型
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut
