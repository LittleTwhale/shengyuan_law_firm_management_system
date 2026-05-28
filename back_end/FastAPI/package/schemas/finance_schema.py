# schemas/finance_schema.py
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from .user import UserOut
from .case import CasePartyOut

from pydantic import BaseModel, Field


# ==========================================
# 1. 财务流水记录 (Financial Record) Schemas
# ==========================================

class FinancialRecordBase(BaseModel):
    """流水记录的基础字段"""
    record_type: str = Field(..., description="类型: income(收款), refund(退费)")
    amount: Decimal = Field(..., description="金额")
    transaction_date: date = Field(..., description="发生日期")
    payer: Optional[str] = Field(None, description="付款人/收款人")
    payment_method: Optional[str] = Field(None, description="支付方式")
    remarks: Optional[str] = Field(None, description="备注")


class FinancialRecordCreate(FinancialRecordBase):
    """创建流水时的入参"""
    finance_id: int = Field(..., description="关联的财务总表ID")


class FinancialRecordResponse(FinancialRecordBase):
    """返回给前端的流水详情"""
    id: int
    operator_id: Optional[int]
    operator_name: Optional[str] = None  # 需要在CRUD层手动填充或通过ORM获取
    created_at: datetime

    class Config:
        from_attributes = True  # 允许从 ORM 模型读取数据


# ==========================================
# 2. 发票记录 (Invoice Record) Schemas
# ==========================================

class InvoiceRecordBase(BaseModel):
    """发票记录的基础字段"""
    invoice_amount: Decimal = Field(..., description="开票金额")
    invoice_date: date = Field(..., description="开票日期")
    invoice_number: Optional[str] = Field(None, description="发票号码")
    invoice_title: Optional[str] = Field(None, description="发票抬头")
    tax_number: Optional[str] = Field(None, description="税号")
    remarks: Optional[str] = Field(None, description="备注")


class InvoiceRecordCreate(InvoiceRecordBase):
    """创建发票时的入参"""
    finance_id: int = Field(..., description="关联的财务总表ID")


class InvoiceRecordResponse(InvoiceRecordBase):
    """返回给前端的发票详情"""
    id: int
    operator_id: Optional[int]
    operator_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ==========================================
# 3. 律师领款记录 (Lawyer Withdrawal) Schemas
# ==========================================

class LawyerWithdrawalBase(BaseModel):
    """领款记录的基础字段"""
    amount: Decimal = Field(..., description="领款金额")
    withdrawal_date: date = Field(..., description="领款日期")
    remarks: Optional[str] = Field(None, description="备注")

class LawyerWithdrawalCreate(LawyerWithdrawalBase):
    """创建领款时的入参"""
    finance_id: int = Field(..., description="关联的财务总表ID")
    lawyer_id: int = Field(..., description="领款律师ID")

class LawyerWithdrawalResponse(LawyerWithdrawalBase):
    """返回给前端的领款详情"""
    id: int
    lawyer_id: int
    lawyer_name: Optional[str] = None  # 用于前端展示律师姓名
    operator_id: Optional[int]
    operator_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# 4. 案件财务总表 (Case Finance) Schemas
# ==========================================
class CaseSimpleInfo(BaseModel):
    """简化案件基础信息"""
    case_number: Optional[str] = None
    main_lawyer: UserOut
    parties: List[CasePartyOut] = Field(default_factory=list, description="当事人列表 / Case parties")

    class Config:
        from_attributes = True

class CaseFinanceBase(BaseModel):
    """财务总表的基础字段"""
    contract_amount: Decimal = Field(0, description="合同规定金额")
    final_contract_amount: Decimal = Field(0, description="合同最终收费金额")
    risk_agency_content: Optional[str] = Field(None, description="风险代理约定内容")
    remarks: Optional[str] = Field(None, description="财务备注")


class CaseFinanceUpdate(CaseFinanceBase):
    """
    更新财务总表时的入参
    """
    unpaid_amount: Optional[Decimal] = Field(None, description="手动修正未付金额")
    uninvoiced_amount: Optional[Decimal] = Field(None, description="手动修正未开票金额")


class CaseFinanceResponse(CaseFinanceBase):
    """返回给前端的财务总览"""
    id: int
    case_id: int
    # 关联的案件简要信息
    case: Optional[CaseSimpleInfo] = None

    # 自动统计字段
    total_invoiced_amount: Decimal
    total_received_amount: Decimal
    total_refund_amount: Decimal
    total_withdrawal_amount: Decimal = Field(0, description="累计律师领款金额")
    uninvoiced_amount: Decimal
    unpaid_amount: Decimal

    created_at: datetime
    updated_at: datetime

    records: List[FinancialRecordResponse] = []
    invoices: List[InvoiceRecordResponse] = []
    withdrawals: List[LawyerWithdrawalResponse] = []

    class Config:
        from_attributes = True

# [分页返回结构的 Schema
class CaseFinancePagination(BaseModel):
    total: int
    items: List[CaseFinanceResponse]


# ==========================================
# 4. 统计报表 (Statistics) Schemas (用于图表或总计)
# ==========================================

class FinanceStatsQuery(BaseModel):
    """统计查询参数"""
    keyword: Optional[str] = None
    start_date: Optional[date]
    end_date: Optional[date]
    year: Optional[int]
    lawyer_id: Optional[int]
    case_category: Optional[str]


class FinanceStatsResponse(BaseModel):
    """统计结果返回"""
    total_income: Decimal = 0  # 总回款
    total_invoiced: Decimal = 0  # 总开票
    total_contract: Decimal = 0  # 总合同额
    count_records: int = 0  # 笔数