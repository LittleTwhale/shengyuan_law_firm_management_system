# schemas/case.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from .user import UserOut

# 银行案件细节
# 银行案件基础模型 - 包含银行相关案件的所有基本字段
class BankCaseBase(BaseModel):
    # --- 借贷基础信息 ---

    # 支行名称
    branch_name: Optional[str] = None
    # 案件状态
    case_status: Optional[str] = Field(None, description="案件状态")
    # 银行要求案件状态
    bank_required_case_status: Optional[str] = Field(None, description="银行要求案件状态")
    # 抵/质押物信息
    collateral_info: Optional[str] = None
    # 抵押物位置
    collateral_location: Optional[str] = None
    # 客户经理
    account_manager: Optional[str] = None
    # 贷款类型
    loan_type: Optional[str] = None
    # 贷款账号
    loan_account: Optional[str] = None

    # --- 金额相关 ---

    # 贷款本金
    loan_principal: Optional[Decimal] = 0
    # 诉讼标的金额(含利息)
    litigation_target_amount: Optional[Decimal] = 0
    # 信用卡违约金
    credit_card_penalty: Optional[Decimal] = 0

    # --- 关键日期与流程 ---

    # 借款日
    loan_date: Optional[date] = None
    # 到期日
    loan_due_date: Optional[date] = None
    # 诉讼时效
    statute_of_limitations: Optional[date] = None
    # 保证到期日
    guarantee_due_date: Optional[date] = None
    # 收案日期
    case_acceptance_date: Optional[date] = None

    # --- 诉讼流程细节 ---

    # 取材料人
    material_fetcher: Optional[str] = None
    # 缺少具体材料
    missing_specific_materials: Optional[str] = Field(None, description="缺少具体材料")
    # 诉前催收情况
    pre_litigation_collection: Optional[str] = None
    # 盖章日
    seal_date: Optional[date] = None
    # 材料提交法院日
    material_submission_date: Optional[date] = None
    # 承办法官
    handling_judge: Optional[str] = None

    # --- 裁判结果补充 ---

    # 裁判时间
    judgment_date: Optional[date] = None
    # 裁判方式
    judgment_method: Optional[str] = None
    # 裁判摘要
    judgment_summary: Optional[str] = None
    # 支持律师费金额
    lawyer_fee_supported: Optional[Decimal] = 0
    # 被告支付律师费金额
    defendant_paid_lawyer_fee: Optional[Decimal] = 0
    # 是否还清
    is_settled: bool = False
    # 是否有二审、再审
    has_second_instance_or_retrial: bool = False

    # --- 执行阶段详情 ---

    # 执行案号
    execution_case_number: Optional[str] = None
    # 执行立案时间
    execution_filing_date: Optional[date] = None
    # 执行法官
    execution_judge: Optional[str] = None
    # 借款人工作单位
    borrower_work_unit: Optional[str] = None
    # 是否为恢复执行
    is_execution_recovery: bool = False
    # 收取执行材料时间
    execution_material_receipt_date: Optional[date] = None
    # 执行材料提交法院时间
    execution_material_submission_date: Optional[date] = None
    # 执行本金金额
    execution_principal: Optional[Decimal] = 0
    # 执行律师费金额
    execution_lawyer_fee: Optional[Decimal] = 0

    # --- 查控与财产 ---

    # 财产调查情况
    property_investigation: Optional[str] = None
    # 网络查控财产情况
    network_control_status: Optional[str] = None
    # 承办人执行方案
    execution_plan: Optional[str] = None
    # 法院执行措施
    court_execution_measures: Optional[str] = None

    # --- 查封与冻结 ---

    # 查封冻结时间（旧字段）
    seizure_freeze_date: Optional[date] = None
    # 冻结开始日期
    freeze_start_date: Optional[date] = None
    # 冻结截止日期
    freeze_end_date: Optional[date] = None
    # 查封开始日期
    seizure_start_date: Optional[date] = None
    # 查封截止日期
    seizure_end_date: Optional[date] = None

    # --- 拍卖流程 ---

    # 拍卖程序
    auction_status: Optional[str] = None
    # 拍卖变卖成交价
    auction_deal_price: Optional[Decimal] = 0

    # --- 结案与终本 ---

    # 执行和解内容
    execution_settlement_content: Optional[str] = None
    # 执行和解到期日
    execution_settlement_due_date: Optional[date] = None
    # 执行和解案件履行跟踪情况
    execution_settlement_tracking: Optional[str] = None
    # 终本时间
    procedure_termination_date: Optional[date] = None
    # 终本原因
    termination_reason: Optional[str] = None
    # 终结执行时间
    execution_conclusion_date: Optional[date] = None
    # 恢复执行时间
    execution_recovery_date: Optional[date] = None
    # 还清时间
    payoff_date: Optional[date] = None

    # --- 回款统计 ---

    # 执行回款总金额
    execution_collection_amount: Optional[Decimal] = 0
    # 执行回款来源
    collection_source: Optional[str] = None

    # --- 复杂记录 (JSON) ---

    # 执行和解跟进及回款额
    execution_settlement_log: Optional[List[Dict[str, Any]]] = []
    # 扣划跟进及回款额
    deduction_log: Optional[List[Dict[str, Any]]] = []
    # 调解案件履行跟踪情况
    mediation_tracking: Optional[str] = None

# 银行案件创建模型
class BankCaseCreate(BankCaseBase):
    pass

# 银行案件更新模型
class BankCaseUpdate(BankCaseBase):
    pass

# 银行案件输出模型
class BankCaseOut(BankCaseBase):
    # 案件唯一标识符
    case_id: int

    class Config:
        # 允许从ORM对象属性创建Pydantic模型实例
        from_attributes = True

# 案件当事人基础模型
class CasePartyBase(BaseModel):
    party_type: str = Field(..., description="类型：原告/被告/第三人等")
    name: str = Field(..., description="姓名")
    id_number: Optional[str] = Field(None, description="身份证号")
    phone: Optional[str] = Field(None, description="电话")
    address: Optional[str] = Field(None, description="地址")
    legal_representative: Optional[str] = Field(None, description="法定代表人")

class CasePartyCreate(CasePartyBase):
    pass

class CasePartyOut(CasePartyBase):
    id: int
    case_id: int
    class Config:
        from_attributes = True

# 创建案件
class CaseCreate(BaseModel):
    # 基本信息
    case_number: Optional[str] = Field(None, description="案件号（批量导入时指定，留空则由系统自动生成）")
    commission_date: Optional[date] = Field(None, description="委托日期")
    case_category: str = Field(..., description="案件类别")
    case_source: Optional[str] = Field(None, description="案件来源")
    fee_method: Optional[str] = Field(None, description="收费方式")
    risk_ratio: Optional[str] = Field(None, description="风险比例")
    case_income: Optional[Decimal] = Field(0, description="案件收入")

    # 诉讼相关
    payment_due_date: Optional[date] = None
    cause: Optional[str] = None
    stage: Optional[str] = None
    investigative_agency: Optional[str] = Field(None, description="侦查机关")
    procuratorate: Optional[str] = Field(None, description="检察院")
    second_instance_procuratorate: Optional[str] = Field(None, description="二审检察机关")
    details: Optional[str] = None

    # 律师信息
    main_lawyer_id: Optional[int] = Field(None, description="主办律师ID")
    assistant_lawyer_id: Optional[int] = None
    assistant_lawyer_2_id: Optional[int] = None
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
    advisory_due_date: Optional[date] = Field(None, description="顾问到期日 / Advisory due date")

    class Config:
        from_attributes = True

    bank_case_details: Optional[BankCaseCreate] = None
    parties: Optional[List[CasePartyCreate]] = []

# 案件更新（部分字段可选）
class CaseUpdate(BaseModel):
    # 基本信息 / Basic info
    commission_date: Optional[date] = Field(None, description="委托日期 / Commission date")
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
    investigative_agency: Optional[str] = Field(None, description="侦查机关 / Investigative Agency")
    procuratorate: Optional[str] = Field(None, description="检察院 / Procuratorate")
    second_instance_procuratorate: Optional[str] = Field(None,description="二审检察机关 / Second Instance Procuratorate")
    details: Optional[str] = Field(None, description="案件详情 / Case details")

    # 律师分配 / Lawyers
    main_lawyer_id: Optional[int] = Field(None, description="主办律师ID / Main lawyer ID")
    assistant_lawyer_id: Optional[int] = Field(None, description="助理律师ID / Assistant lawyer ID")
    assistant_lawyer_2_id: Optional[int] = Field(None, description="第二助理律师ID / Assistant lawyer 2 ID")
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
    advisory_due_date: Optional[date] = Field(None, description="顾问到期日 / Advisory due date")

    class Config:
        from_attributes = True

    bank_case_details: Optional[BankCaseUpdate] = None
    parties: Optional[List[CasePartyCreate]] = None

# 案件返回给前端
class CaseOut(BaseModel):
    # 基本信息
    case_id: int = Field(..., description="案件ID / Case ID")
    case_number: str = Field(..., description="案件号 / Case number")
    commission_date: Optional[date] = Field(None, description="委托日期 / Commission date")
    case_category: str = Field(..., description="案件类别 / Case category")
    case_source: Optional[str] = Field(None, description="案件来源 / Case source")
    fee_method: Optional[str] = Field(None, description="收费方式 / Fee method")
    risk_ratio: Optional[str] = Field(None, description="风险比例 / Risk ratio")
    case_income: Optional[Decimal] = Field(0, description="案件收入 / Case income")

    # 诉讼相关
    payment_due_date: Optional[date] = Field(None, description="付款到期日 / Payment due date")
    cause: Optional[str] = Field(None, description="案由 / Cause")
    stage: Optional[str] = Field(None, description="介入阶段 / Case stage")
    investigative_agency: Optional[str] = Field(None, description="侦查机关 / Investigative Agency")
    procuratorate: Optional[str] = Field(None, description="检察院 / Procuratorate")
    second_instance_procuratorate: Optional[str] = Field(None,description="二审检察机关 / Second Instance Procuratorate")
    agency_power: Optional[str] = Field(None, description="代理权限 / Agency power")
    court: Optional[str] = Field(None, description="审理法院 / Court")
    hearing_date: Optional[date] = Field(None, description="开庭时间 / Hearing date")
    filing_date: Optional[date] = Field(None, description="立案日 / Filing date")
    closing_date: Optional[date] = Field(None, description="结案时间 / Closing date")
    location: Optional[str] = Field(None, description="案件地点 / Case location")
    details: Optional[str] = Field(None, description="案件详情 / Case details")

    # 状态与标记
    review_status: str = Field(..., description="案件审核状态 / Review status")
    review_comment: Optional[str] = Field(None, description="审核意见/修改建议 / Review comment")
    is_major: bool = Field(False, description="是否重大 / Is major")
    has_paper_file: bool = Field(False, description="是否纸质卷宗 / Has paper file")
    is_dismissed: bool = Field(False, description="是否解除 / Is dismissed")
    has_record: bool = Field(False, description="是否笔录 / Has record")
    has_preservation: bool = Field(False, description="是否保全 / Has preservation")

    preservation_start: Optional[date] = Field(None, description="保全开始日 / Preservation start date")
    preservation_end: Optional[date] = Field(None, description="保全终止日 / Preservation end date")

    # 结案与执行
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
    advisory_due_date: Optional[date] = Field(None, description="顾问到期日 / Advisory due date")

    # 律师信息
    main_lawyer: Optional[UserOut] = None
    assistant_lawyer: Optional[UserOut] = None
    assistant_lawyer_2: Optional[UserOut] = None
    execution_lawyer: Optional[UserOut] = None
    execution_assistant: Optional[UserOut] = None
    reviewer: Optional[UserOut] = None

    # 时间戳
    created_at: datetime = Field(..., description="创建时间 / Created at")
    updated_at: datetime = Field(..., description="更新时间 / Updated at")

    class Config:
        from_attributes = True

    bank_case_details: Optional[BankCaseOut] = None
    parties: List[CasePartyOut] = []

# 单条案件模型
class CaseSimpleOut(BaseModel):
    case_id: int = Field(..., description="案件ID / Case ID")
    case_number: str = Field(..., description="案件号 / Case number")
    client_name: Optional[str] = Field(None, description="委托人（从 CaseParty 聚合） / Client name")
    borrower_name: Optional[str] = Field(None, description="借款人 / Borrower name")
    case_category: str = Field(..., description="案件类别 / Case category")
    case_status: Optional[str] = Field(None, description="案件状态 / Case status")
    case_code: Optional[str] = Field(None, description="法院案号 / Court case code")
    review_status: str = Field(..., description="案件审核状态 / Review status")
    review_comment: Optional[str] = Field(None, description="审核意见/修改建议 / Review comment")
    reviewed_at: Optional[datetime] = Field(None, description="审核时间 / Reviewed at")
    main_lawyer: Optional[UserOut] = Field(None, description="主办律师 / Main lawyer")
    execution_lawyer: Optional[UserOut] = Field(None, description="执行主办律师 / Execution lawyer")
    litigation_fee_payment_amount: Optional[Decimal] =Field(0, description="诉讼费缴费金额 / Litigation fee payment amount")
    litigation_fee_refund_amount: Optional[Decimal] = Field(0, description="诉讼费退费金额 / Litigation fee refund amount")
    created_at: datetime = Field(..., description="创建时间 / Created at")
    parties: List[CasePartyOut] = Field(default_factory=list, description="当事人列表 / Case parties")

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


# 事件提醒
class EventReminderOut(BaseModel):
    case_id: Optional[int] = None
    case_number: Optional[str] = None
    client_name: Optional[str] = None

    event_type: str = Field(..., description="事件类型：开庭/保全/调解/执行 或者 自定义标题")
    event_date: date = Field(..., description="事件日期")
    days_remaining: int = Field(..., description="剩余天数")

    source: str = Field("case", description="数据来源：case(系统提取) / custom(用户自定义)")
    schedule_id: Optional[int] = Field(None, description="自定义日程记录的ID，用于编辑/删除")
    description: Optional[str] = Field(None, description="自定义日程的具体说明")

    class Config:
        from_attributes = True

# 自定义日程创建
class UserScheduleCreate(BaseModel):
    title: str = Field(..., description="日程标题/事项类型")
    event_date: date = Field(..., description="提醒日期")
    description: Optional[str] = Field(None, description="详细描述/备注")
    related_case_id: Optional[int] = Field(None, description="关联的业务ID(可选)")

# 自定义日程更新
class UserScheduleUpdate(BaseModel):
    title: Optional[str] = Field(None, description="日程标题/事项类型")
    event_date: Optional[date] = Field(None, description="提醒日期")
    description: Optional[str] = Field(None, description="详细描述/备注")
    related_case_id: Optional[int] = Field(None, description="关联的业务ID(可选)")

# 业务导出查询参数
class CaseExportQuery(BaseModel):
    keyword: Optional[str] = None
    case_category: Optional[str] = None
    main_lawyer_id: Optional[int] = None
    execution_lawyer_id: Optional[int] = None
    client_name: Optional[str] = None
    year: Optional[str] = None
    case_status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    case_ids: Optional[List[int]] = None

# 批量审核请求
class BatchReviewRequest(BaseModel):
    case_ids: List[int]
    review_status: str
    force_ids: List[int] = []  # 存放需要强制忽略冲突的案件ID
    review_comment: Optional[str] = Field(None, description="审核意见/修改建议")