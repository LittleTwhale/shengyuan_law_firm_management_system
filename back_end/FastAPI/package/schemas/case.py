# schemas/case.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from .user import UserOut

# 案件基础信息
class CaseBase(BaseModel):
    commission_date: date = Field(..., description="委托日期")
    client_name: str = Field(..., description="委托人")
    client_id_number: str = Field(..., description="委托人身份证号/单位税号")
    client_phone: Optional[str] = Field(None, description="委托人电话")
    case_category: str = Field(..., description="案件类别")
    is_bank_case: bool = Field(False, description="是否为银行案件")
    case_source: Optional[str] = Field(None, description="案件来源")
    fee_method: Optional[str] = Field(None, description="收费方式")
    risk_ratio: Optional[str] = Field(None, description="风险比例")
    case_income: Optional[Decimal] = Field(0, description="案件收入")
    cause: Optional[str] = Field(None, description="案由")
    stage: Optional[str] = Field(None, description="介入阶段")


# 创建案件
class CaseCreate(CaseBase):
    main_lawyer_id: int = Field(..., description="主办律师ID")


# 案件更新（部分字段可选）
class CaseUpdate(BaseModel):
    commission_date: Optional[date] = None
    client_name: Optional[str] = None
    client_id_number: Optional[str] = None
    client_phone: Optional[str] = None
    case_category: Optional[str] = None
    is_bank_case: Optional[bool] = None
    case_source: Optional[str] = None
    fee_method: Optional[str] = None
    risk_ratio: Optional[str] = None
    case_income: Optional[Decimal] = None
    cause: Optional[str] = None
    stage: Optional[str] = None


# 案件返回给前端
class CaseOut(CaseBase):
    case_id: int = Field(..., description="案件ID")
    case_number: str = Field(..., description="案件号")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    main_lawyer: UserOut
    assistant_lawyer: Optional[UserOut] = None
    execution_lawyer: Optional[UserOut] = None
    execution_assistant: Optional[UserOut] = None

    class Config:
        from_attributes = True

# 单条案件模型
class CaseSimpleOut(CaseBase):
    case_id: int
    case_number: str

    class Config:
        from_attributes = True

# 案件分页模型
class CasePageOut(BaseModel):
    total: int
    items: List[CaseSimpleOut]
