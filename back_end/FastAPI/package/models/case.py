# models/case.py
from sqlalchemy import Column, Integer, String, Enum, Boolean, DECIMAL, Date, Text, ForeignKey, TIMESTAMP, func, JSON
from ..database.database import Base
from sqlalchemy.orm import relationship


class Case(Base):
    __tablename__ = "cases"

    # 基本信息
    case_id = Column(Integer, primary_key=True, index=True, comment="案件ID，自增主键")
    case_number = Column(String(50), unique=True, nullable=False, comment="案件号")
    commission_date = Column(Date, nullable=False, comment="委托日期")
    client_name = Column(String(100), nullable=False, comment="委托人")
    client_id_number = Column(String(18), nullable=True, comment="委托人身份证号/单位税号")
    client_phone = Column(String(20), nullable=True, comment="委托人电话")

    case_category = Column(Enum('民事案件','银行案件','刑事案件','行政案件','非诉业务','劳动仲裁','商事仲裁','法律顾问业务','法律援助(民事)','法律援助(刑事)','法律援助(行政)'), nullable=False, comment="案件类别")

    case_source = Column(String(100), nullable=True, comment="案件来源")
    fee_method = Column(String(50), nullable=True, comment="收费方式")
    risk_ratio = Column(String(50), nullable=True, comment="风险比例")
    case_income = Column(DECIMAL(10,2), default=0, comment="案件收入")

    payment_due_date = Column(Date, nullable=True, comment="付款到期日")
    cause = Column(Text, nullable=True, comment="案由")
    stage = Column(String(100), nullable=True, comment="介入阶段")

    plaintiff = Column(String(100), nullable=False, comment="原告/申请人")
    appellant_info = Column(Text, nullable=True, comment="上诉人信息补充")
    extra_appellant_info = Column(Text, nullable=True, comment="补上诉人或补告信息补充")
    defendant = Column(String(100), nullable=True, comment="被告")
    third_party = Column(String(255), nullable=True, comment="第三人")
    investigative_agency = Column(String(255), nullable=True, comment="侦查机关")
    procuratorate = Column(String(255), nullable=True, comment="检察院")
    second_instance_procuratorate = Column(String(255), nullable=True, comment="二审检察机关")

    agency_power = Column(Enum('特别代理','一般代理',''), nullable=True, comment="代理权限")
    court = Column(String(100), nullable=True, comment="审理法院")
    hearing_date = Column(Date, nullable=True, comment="开庭时间")
    filing_date = Column(Date, nullable=True, comment="立案日")
    closing_date = Column(Date, nullable=True, comment="结案时间")

    location = Column(String(255), nullable=True, comment="案件地点")
    details = Column(Text, nullable=True, comment="案件详情")

    # 律师信息
    main_lawyer_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="主办律师ID")
    assistant_lawyer_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="助理律师ID")
    execution_lawyer_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="执行主办律师ID")
    execution_assistant_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="执行助理律师ID")

    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="案件审核人ID")

    # 状态与标记
    review_status = Column(Enum('待审核','已审核','已拒绝'), nullable=False, comment="案件审核状态")

    is_major = Column(Boolean, default=False, nullable=False, comment="是否重大")
    has_paper_file = Column(Boolean, default=False, nullable=False, comment="是否纸质卷宗")
    is_dismissed = Column(Boolean, default=False, nullable=False, comment="是否解除")
    has_record = Column(Boolean, default=False, nullable=False, comment="是否笔录")
    has_preservation = Column(Boolean, default=False, nullable=False, comment="是否保全")

    is_deleted = Column(Boolean, default=False, nullable=False, comment="是否删除")

    preservation_start = Column(Date, nullable=True, comment="保全开始日")
    preservation_end = Column(Date, nullable=True, comment="保全终止日")

    case_code = Column(String(50), nullable=True, comment="案号")
    closing_status = Column(String(50), nullable=True, comment="结案状态")
    closing_method = Column(String(50), nullable=True, comment="结案方式")

    litigation_fee_payment_date = Column(Date, nullable=True, comment="诉讼费缴费时间")
    litigation_fee_payment_amount = Column(DECIMAL(10,2), default=0, comment="诉讼费缴费金额")
    litigation_fee_refund_date = Column(Date, nullable=True, comment="诉讼费退费时间")
    litigation_fee_refund_amount = Column(DECIMAL(10,2), default=0, comment="诉讼费退费金额")

    execution_application_date = Column(Date, nullable=True, comment="申请执行日")
    mediation_due_date = Column(Date, nullable=True, comment="调解到期日")
    execution_due_date = Column(Date, nullable=True, comment="执行到期日")

    # 时间戳
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.now(), server_onupdate=func.now(), comment="更新时间")

    # ORM 关系
    main_lawyer = relationship("User", back_populates="main_cases", foreign_keys="Case.main_lawyer_id")
    assistant_lawyer = relationship("User", back_populates="assistant_cases", foreign_keys="Case.assistant_lawyer_id")
    execution_lawyer = relationship("User", back_populates="execution_cases", foreign_keys="Case.execution_lawyer_id")
    execution_assistant = relationship("User", back_populates="execution_assistant_cases",
                                       foreign_keys="Case.execution_assistant_id")
    reviewer = relationship("User", foreign_keys="Case.reviewer_id")
    # 财务信息
    finance = relationship("CaseFinance", back_populates="case", uselist=False, cascade="all, delete-orphan")
    # 电子卷宗关联
    volumes = relationship("CaseVolume", back_populates="case", cascade="all, delete-orphan",
                           order_by="CaseVolume.sort_order")
    # 银行案件细节
    bank_case_details = relationship("BankCase", back_populates="case", uselist=False, cascade="all, delete-orphan")
    # 当事人
    parties = relationship("CaseParty", back_populates="case", cascade="all, delete-orphan")


class BankCase(Base):
    __tablename__ = "bank_cases"

    case_id = Column(Integer, ForeignKey("cases.case_id"), primary_key=True, comment="关联主案件表ID")

    # 借贷基础信息
    branch_name = Column(String(100), comment="支行名称")
    borrower_id_number = Column(String(50), comment="借款人身份证号码/统信代码")
    guarantor = Column(String(255), comment="担保人")
    collateral_info = Column(Text, comment="抵/质押物信息")
    collateral_location = Column(String(255), comment="抵押物位置")
    is_inclusive_finance = Column(Boolean, default=False, comment="是否普惠金融")
    account_manager = Column(String(50), comment="客户经理")

    # 金额相关
    loan_principal = Column(DECIMAL(15, 2), default=0, comment="贷款本金")
    litigation_target_amount = Column(DECIMAL(15, 2), default=0, comment="诉讼标的金额(含利息)")
    credit_card_penalty = Column(DECIMAL(15, 2), default=0, comment="信用卡违约金")

    # 关键日期
    loan_date = Column(Date, comment="借款日")
    loan_due_date = Column(Date, comment="到期日")
    overdue_date = Column(Date, comment="逾期时间")
    statute_of_limitations = Column(String(100), comment="诉讼时效")

    # 诉讼流程细节
    material_fetcher = Column(String(50), comment="取材料人")
    pre_litigation_collection = Column(Text, comment="诉前催收情况")
    seal_date = Column(Date, comment="盖章日")
    material_submission_date = Column(Date, comment="材料提交法院日")

    # 裁判结果补充
    judgment_summary = Column(Text, comment="裁判摘要")
    lawyer_fee_supported = Column(DECIMAL(15, 2), default=0, comment="支持律师费金额")
    defendant_paid_lawyer_fee = Column(DECIMAL(15, 2), default=0, comment="被告支付律师费金额")
    is_settled = Column(Boolean, default=False, comment="是否还清")

    # 执行阶段详情
    execution_case_number = Column(String(50), comment="执行案号")
    execution_filing_date = Column(Date, comment="执行立案时间")
    execution_judge = Column(String(50), comment="执行法官")
    borrower_work_unit = Column(String(100), comment="借款人工作单位")
    is_execution_recovery = Column(Boolean, default=False, comment="是否为恢复执行")

    execution_principal = Column(DECIMAL(15, 2), default=0, comment="执行本金金额")
    execution_lawyer_fee = Column(DECIMAL(15, 2), default=0, comment="执行律师费金额")

    # 查控与财产
    property_investigation = Column(Text, comment="财产调查情况")
    network_control_status = Column(Text, comment="网络查控财产情况")
    execution_plan = Column(Text, comment="承办人执行方案")
    court_execution_measures = Column(Text, comment="法院执行措施")

    # 查封与冻结 (建议存JSON字符串)
    seizure_freeze_info = Column(Text, comment="查封冻结标的及时间")

    # 拍卖流程
    auction_status = Column(Text, comment="拍卖程序")
    auction_deal_price = Column(DECIMAL(15, 2), default=0, comment="拍卖变卖成交价")

    # 结案与终本
    execution_settlement_content = Column(Text, comment="执行和解内容")
    procedure_termination_date = Column(Date, comment="终本时间")
    termination_reason = Column(Text, comment="终本原因")
    execution_conclusion_date = Column(Date, comment="终结执行时间")
    execution_recovery_date = Column(Date, comment="恢复执行时间")
    payoff_date = Column(Date, comment="还清时间")

    # 回款统计
    execution_collection_amount = Column(DECIMAL(15, 2), default=0, comment="执行回款总金额")
    collection_source = Column(String(100), comment="执行回款来源")

    # 复杂记录 (JSON)
    execution_settlement_log = Column(JSON, comment="执行和解跟进及回款额")
    deduction_log = Column(JSON, comment="扣划跟进及回款额")
    mediation_tracking = Column(Text, comment="调解案件履行跟踪情况")

    # 关系
    case = relationship("Case", back_populates="bank_case_details")


class CaseParty(Base):
    __tablename__ = "case_parties"

    id = Column(Integer, primary_key=True, index=True, comment="当事人ID")
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False, comment="关联案件ID")

    # 核心字段
    party_type = Column(String(50), nullable=False, comment="当事人类型：委托人、原告、被告、第三人等")
    name = Column(String(100), nullable=False, comment="姓名/名称")

    # 详细信息
    id_number = Column(String(50), nullable=True, comment="身份证号/统一社会信用代码")
    phone = Column(String(50), nullable=True, comment="联系电话")
    address = Column(Text, nullable=True, comment="住所地/通讯地址")
    legal_representative = Column(String(50), nullable=True, comment="法定代表人")

    # 时间戳
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.now(), server_onupdate=func.now(), comment="更新时间")

    # 建立与 Case 的反向关系
    case = relationship("Case", back_populates="parties")