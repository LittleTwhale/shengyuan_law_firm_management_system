# schemas/case_operation.py
from pydantic import BaseModel, Field
from typing import Optional, Any, List, Dict
from datetime import datetime


# 基础 schema
class CaseOperationBase(BaseModel):
    case_id: Optional[int] = Field(None, description="关联案件ID（新增时可为空）")
    user_id: int = Field(..., description="操作用户ID")
    user_name: Optional[str] = Field(None, description="操作用户姓名")
    operation_type: str = Field(..., description="操作类型：新增/修改/删除")
    pending_data: Optional[Any] = Field(None, description="待审核的数据（JSON 格式）")


# 创建操作记录（用户提交操作时用）
class CaseOperationCreate(CaseOperationBase):
    pass


# 更新操作记录（主要用于管理员审核时修改状态/备注）
class CaseOperationUpdate(BaseModel):
    review_status: Optional[str] = Field(None, description="审核状态：待审核/已通过/已拒绝")
    review_user_id: Optional[int] = Field(None, description="审核人ID")
    review_remark: Optional[str] = Field(None, description="审核备注")
    reviewed_at: Optional[datetime] = Field(None, description="审核时间")


# 返回给前端的完整结构
class CaseOperationOut(CaseOperationBase):
    # 模型配置 - 启用从 ORM 属性加载数据
    model_config = {
        "from_attributes": True
    }

    operation_id: int = Field(..., description="操作ID")
    review_status: str = Field(..., description="审核状态")
    review_user_id: Optional[int] = Field(None, description="审核人ID")
    review_user_name: Optional[str] = Field(None, description="审核人姓名")
    review_remark: Optional[str] = Field(None, description="审核备注")
    reviewed_at: Optional[datetime] = Field(None, description="审核时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    # 解析后的操作内容
    details: Optional[List[Dict[str, Any]]] = Field(None, description="操作字段变化列表")
