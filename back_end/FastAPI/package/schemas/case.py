# schemas/case.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date, datetime
from decimal import Decimal
from .user import UserOut

# 创建案件
class CaseCreate(BaseModel):
    # 🧾 基本信息
    commission_date: date = Field(..., description="委托日期")
    client_name: str = Field(..., description="委托人")
    client_id_number: Optional[str] = Field(None, description="委托人身份证号/单位税号")
    client_phone: Optional[str] = Field(None, description="委托人电话")
    case_category: str = Field(..., description="案件类别")
    case_source: Optional[str] = Field(None, description="案件来源")
    fee_method: Optional[str] = Field(None, description="收费方式")
    risk_ratio: Optional[str] = Field(None, description="风险比例")
    case_income: Optional[Decimal] = Field(0, description="案件收入")

    # ⚖️ 诉讼相关
    payment_due_date: Optional[date] = None
    cause: Optional[str] = None
    stage: Optional[str] = None
    plaintiff: Optional[str] = None
    appellant_info: Optional[str] = None
    extra_appellant_info: Optional[str] = None
    defendant: Optional[str] = None
    details: Optional[str] = None

    # 👩‍💼 律师信息
    main_lawyer_id: int = Field(..., description="主办律师ID")
    assistant_lawyer_id: Optional[int] = None
    execution_lawyer_id: Optional[int] = None
    execution_assistant_id: Optional[int] = None

    # 代理/审理信息
    agency_power: Optional[str] = None
    court: Optional[str] = None
    hearing_date: Optional[date] = None
    filing_date: Optional[date] = None
    closing_date: Optional[date] = None

    # 状态与标记
    is_major: bool = False
    has_paper_file: bool = False
    is_dismissed: bool = False
    has_record: bool = False
    has_preservation: bool = False

    preservation_start: Optional[date] = None
    preservation_end: Optional[date] = None

    location: Optional[str] = None

    # 结案与执行
    case_code: Optional[str] = None
    closing_status: Optional[str] = None
    closing_method: Optional[str] = None

    # 诉讼费
    litigation_fee_payment_date: Optional[date] = None
    litigation_fee_payment_amount: Optional[Decimal] = 0
    litigation_fee_refund_date: Optional[date] = None
    litigation_fee_refund_amount: Optional[Decimal] = 0

    # 执行相关
    execution_application_date: Optional[date] = None
    mediation_due_date: Optional[date] = None
    execution_due_date: Optional[date] = None

    class Config:
        from_attributes = True


# 案件更新（部分字段可选）
class CaseUpdate(BaseModel):
    # 基本信息 / Basic info
    commission_date: Optional[date] = Field(None, description="委托日期 / Commission date")
    client_name: Optional[str] = Field(None, description="委托人 / Client name")
    client_id_number: Optional[str] = Field(None, description="委托人身份证号/单位税号 / Client ID / Tax number")
    client_phone: Optional[str] = Field(None, description="委托人电话 / Client phone")
    case_category: Optional[str] = Field(None, description="案件类别 / Case category")
    case_source: Optional[str] = Field(None, description="案件来源 / Case source")
    fee_method: Optional[str] = Field(None, description="收费方式 / Fee method")
    risk_ratio: Optional[str] = Field(None, description="风险比例 / Risk ratio")
    case_income: Optional[Decimal] = Field(None, description="案件收入 / Case income")

    # 费用/支付相关 / Payment-related
    payment_due_date: Optional[date] = Field(None, description="付款到期日 / Payment due date")

    # 案件主体 / Case parties & details
    cause: Optional[str] = Field(None, description="案由 / Cause")
    stage: Optional[str] = Field(None, description="介入阶段 / Case stage")
    plaintiff: Optional[str] = Field(None, description="原告 / Plaintiff")
    appellant_info: Optional[str] = Field(None, description="上诉人信息 / Appellant info")
    extra_appellant_info: Optional[str] = Field(None, description="被上诉人信息 / Extra appellant info")
    defendant: Optional[str] = Field(None, description="被告 / Defendant")
    details: Optional[str] = Field(None, description="案件详情 / Case details")

    # 律师分配 / Lawyers
    main_lawyer_id: Optional[int] = Field(None, description="主办律师ID / Main lawyer ID")
    assistant_lawyer_id: Optional[int] = Field(None, description="助理律师ID / Assistant lawyer ID")
    execution_lawyer_id: Optional[int] = Field(None, description="执行主办律师ID / Execution main lawyer ID")
    execution_assistant_id: Optional[int] = Field(None, description="执行助理ID / Execution assistant ID")

    # 代理/审理信息 / Court & agency
    agency_power: Optional[str] = Field(None, description="代理权限 / Agency power")
    court: Optional[str] = Field(None, description="审理法院 / Court")
    hearing_date: Optional[date] = Field(None, description="开庭时间 / Hearing date")
    filing_date: Optional[date] = Field(None, description="立案日 / Filing date")
    closing_date: Optional[date] = Field(None, description="结案时间 / Closing date")

    # 标记/状态 / Flags & status
    is_major: Optional[bool] = Field(None, description="是否重大 / Is major")
    has_paper_file: Optional[bool] = Field(None, description="是否纸质卷宗 / Has paper file")
    is_dismissed: Optional[bool] = Field(None, description="是否解除 / Is dismissed")
    has_record: Optional[bool] = Field(None, description="是否笔录 / Has record")

    # 保全 / Preservation
    has_preservation: Optional[bool] = Field(None, description="是否保全 / Has preservation")
    preservation_start: Optional[date] = Field(None, description="保全开始日 / Preservation start date")
    preservation_end: Optional[date] = Field(None, description="保全终止日 / Preservation end date")

    # 结案与执行 / Closing & execution
    case_code: Optional[str] = Field(None, description="法院案号 / Court case code")
    closing_status: Optional[str] = Field(None, description="结案状态 / Closing status")
    closing_method: Optional[str] = Field(None, description="结案方式 / Closing method")

    # 诉讼费 / Litigation fee
    litigation_fee_payment_date: Optional[date] = Field(None, description="诉讼费缴费时间 / Litigation fee payment date")
    litigation_fee_payment_amount: Optional[Decimal] = Field(None, description="诉讼费缴费金额 / Litigation fee payment amount")
    litigation_fee_refund_date: Optional[date] = Field(None, description="诉讼费退费时间 / Litigation fee refund date")
    litigation_fee_refund_amount: Optional[Decimal] = Field(None, description="诉讼费退费金额 / Litigation fee refund amount")

    # 执行相关 / Execution related
    execution_application_date: Optional[date] = Field(None, description="申请执行日 / Execution application date")
    mediation_due_date: Optional[date] = Field(None, description="调解到期日 / Mediation due date")
    execution_due_date: Optional[date] = Field(None, description="执行到期日 / Execution due date")

    class Config:
        from_attributes = True


# 案件返回给前端
class CaseOut(BaseModel):
    # 🧾 基本信息
    case_id: int = Field(..., description="案件ID / Case ID")
    case_number: str = Field(..., description="案件号 / Case number")
    commission_date: date = Field(..., description="委托日期 / Commission date")
    client_name: str = Field(..., description="委托人 / Client name")
    client_id_number: Optional[str] = Field(None, description="身份证号/税号 / ID or Tax number")
    client_phone: Optional[str] = Field(None, description="电话 / Phone number")

    case_category: str = Field(..., description="案件类别 / Case category")
    case_source: Optional[str] = Field(None, description="案件来源 / Case source")
    fee_method: Optional[str] = Field(None, description="收费方式 / Fee method")
    risk_ratio: Optional[str] = Field(None, description="风险比例 / Risk ratio")
    case_income: Optional[Decimal] = Field(0, description="案件收入 / Case income")

    # ⚖️ 诉讼相关
    payment_due_date: Optional[date] = Field(None, description="付款到期日 / Payment due date")
    cause: Optional[str] = Field(None, description="案由 / Cause")
    stage: Optional[str] = Field(None, description="介入阶段 / Case stage")
    plaintiff: Optional[str] = Field(None, description="原告 / Plaintiff")
    appellant_info: Optional[str] = Field(None, description="上诉人信息 / Appellant info")
    extra_appellant_info: Optional[str] = Field(None, description="补上诉人信息 / Extra appellant info")
    defendant: Optional[str] = Field(None, description="被告 / Defendant")
    agency_power: Optional[str] = Field(None, description="代理权限 / Agency power")
    court: Optional[str] = Field(None, description="审理法院 / Court")
    hearing_date: Optional[date] = Field(None, description="开庭时间 / Hearing date")
    filing_date: Optional[date] = Field(None, description="立案日 / Filing date")
    closing_date: Optional[date] = Field(None, description="结案时间 / Closing date")
    location: Optional[str] = Field(None, description="案件地点 / Case location")
    details: Optional[str] = Field(None, description="案件详情 / Case details")

    # ⚙️ 状态与标记
    review_status: str = Field(..., description="案件审核状态 / Review status")
    is_major: bool = Field(False, description="是否重大 / Is major")
    has_paper_file: bool = Field(False, description="是否纸质卷宗 / Has paper file")
    is_dismissed: bool = Field(False, description="是否解除 / Is dismissed")
    has_record: bool = Field(False, description="是否笔录 / Has record")
    has_preservation: bool = Field(False, description="是否保全 / Has preservation")

    preservation_start: Optional[date] = Field(None, description="保全开始日 / Preservation start date")
    preservation_end: Optional[date] = Field(None, description="保全终止日 / Preservation end date")

    # 📅 结案与执行
    case_code: Optional[str] = Field(None, description="案号 / Case code")
    closing_status: Optional[str] = Field(None, description="结案状态 / Closing status")
    closing_method: Optional[str] = Field(None, description="结案方式 / Closing method")

    litigation_fee_payment_date: Optional[date] = Field(None, description="诉讼费缴费时间 / Litigation fee payment date")
    litigation_fee_payment_amount: Optional[Decimal] = Field(0, description="诉讼费缴费金额 / Litigation fee payment amount")
    litigation_fee_refund_date: Optional[date] = Field(None, description="诉讼费退费时间 / Litigation fee refund date")
    litigation_fee_refund_amount: Optional[Decimal] = Field(0, description="诉讼费退费金额 / Litigation fee refund amount")

    execution_application_date: Optional[date] = Field(None, description="申请执行日 / Execution application date")
    mediation_due_date: Optional[date] = Field(None, description="调解到期日 / Mediation due date")
    execution_due_date: Optional[date] = Field(None, description="执行到期日 / Execution due date")

    # 👩‍💼 律师信息
    main_lawyer: UserOut
    assistant_lawyer: Optional[UserOut] = None
    execution_lawyer: Optional[UserOut] = None
    execution_assistant: Optional[UserOut] = None
    reviewer: Optional[UserOut] = None

    # 🕒 时间戳
    created_at: datetime = Field(..., description="创建时间 / Created at")
    updated_at: datetime = Field(..., description="更新时间 / Updated at")

    class Config:
        from_attributes = True

# 单条案件模型
class CaseSimpleOut(BaseModel):
    case_id: int = Field(..., description="案件ID / Case ID")
    case_number: str = Field(..., description="案件号 / Case number")
    client_name: str = Field(..., description="委托人 / Client name")
    case_category: str = Field(..., description="案件类别 / Case category")
    review_status: str = Field(..., description="案件审核状态 / Review status")
    main_lawyer: UserOut = Field(..., description="主办律师 / Main lawyer")
    created_at: datetime = Field(..., description="创建时间 / Created at")

    class Config:
        from_attributes = True

# 案件分页模型
class CasePageOut(BaseModel):
    total: int
    items: List[CaseSimpleOut]

# 个人信息案件统计
class CaseStatistics(BaseModel):
    main_case_count: int = Field(..., description="主办案件数 / Main case count")
    total_income: Decimal = Field(..., description="案件收入 / Case income")
    category_stats: Dict[str, int] = Field(..., description="案件类别统计 / Category statistics")
    review_case_count: Optional[int] = Field(None, description="审核案件数 / Review case count")

    class Config:
        from_attributes = True
