# schemas/user.py
from pydantic import BaseModel, Field
from typing import Optional,Annotated,Dict,Any
from datetime import datetime

# 用户基础信息模型
class UserBase(BaseModel):
    accounts: Annotated[str, Field(min_length=3, max_length=20, description="用户账号")]
    real_name: Optional[str] = Field(None, description="真实姓名")
    role: Optional[str] = Field("user", description="用户角色，可选值: user/admin/owner")
    position: Optional[str] = Field(None, description="用户职位")

# 创建用户模型（含密码）
class UserCreate(UserBase):
    password: Annotated[str, Field(min_length=6, max_length=20, description="用户密码")]

# 用户响应模型（返回给前端，不包含密码）
class UserOut(UserBase):
    id: int = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    # 返回给前端的权限字典，默认为空字典
    permissions: Optional[Dict[str, Any]] = Field(default={}, description="用户细粒度权限配置")

    class Config:
        from_attributes = True  # 告诉 Pydantic 可以读取 ORM 对象

# 登录请求模型
class UserLogin(BaseModel):
    accounts: str = Field(..., description="用户账号")
    password: str = Field(..., description="用户密码")

# 修改密码请求模型
class ChangePasswordRequest(BaseModel):
    user_id: int
    old_password: str
    new_password: str

# Token 响应模型
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

# 用于接收权限更新请求的数据模型
class UserPermissionUpdate(BaseModel):
    # 这里定义具体的权限字段，方便 API 文档生成和参数校验
    # 使用 Optional[bool] = None 允许前端只更新其中一项
    can_review_case: Optional[bool] = Field(None, description="是否允许审核案件")
    can_approve_seal: Optional[bool] = Field(None, description="是否允许审批印章")
    can_access_admin: Optional[bool] = Field(None, description="是否允许访问后台管理")

    # 支持任意动态字段
    class Config:
        extra = "allow"