# models/case.py
from sqlalchemy import Column, Integer, String, Enum, Boolean, DECIMAL, Date, Text, ForeignKey, TIMESTAMP, func
from ..database.database import Base
from sqlalchemy.orm import relationship


class Case(Base):
    __tablename__ = "cases"

    # 基本信息
    case_id = Column(Integer, primary_key=True, index=True, comment="案件ID，自增主键")
    case_number = Column(String(50), unique=True, nullable=False, comment="案件号")
    commission_date = Column(Date, nullable=False, comment="委托日期")
    client_name = Column(String(100), nullable=False, comment="委托人")
    client_id_number = Column(String(18), nullable=False, comment="委托人身份证号/单位税号")
    client_phone = Column(String(20), nullable=True, comment="委托人电话")

    case_category = Column(Enum('民事案件','非诉案件','刑事案件','行政案件','仲裁案件','法律顾问业务'), nullable=False, comment="案件类别")
    is_bank_case = Column(Boolean, default=False, nullable=False, comment="是否为银行案件")

    case_source = Column(String(100), nullable=True, comment="案件来源")
    fee_method = Column(String(50), nullable=True, comment="收费方式")
    risk_ratio = Column(String(50), nullable=True, comment="风险比例")
    case_income = Column(DECIMAL(10,2), default=0, comment="案件收入")

    payment_due_date = Column(Date, nullable=True, comment="付款到期日")
    cause = Column(Text, nullable=True, comment="案由")
    stage = Column(String(100), nullable=True, comment="介入阶段")

    plaintiff = Column(String(100), nullable=False, comment="原告/申请人")
    appellant_info = Column(Text, nullable=True, comment="上诉人或第三人信息补充")
    extra_appellant_info = Column(Text, nullable=True, comment="补上诉人或补告信息补充")
    defendant = Column(String(100), nullable=True, comment="被告")

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

    # 状态与标记
    is_major = Column(Boolean, default=False, nullable=False, comment="是否重大")
    has_paper_file = Column(Boolean, default=False, nullable=False, comment="是否纸质卷宗")
    is_dismissed = Column(Boolean, default=False, nullable=False, comment="是否解除")
    has_record = Column(Boolean, default=False, nullable=False, comment="是否笔录")
    has_preservation = Column(Boolean, default=False, nullable=False, comment="是否保全")

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
    operations = relationship("CaseOperation", back_populates="case")

    main_lawyer = relationship("User", back_populates="main_cases", foreign_keys="Case.main_lawyer_id")
    assistant_lawyer = relationship("User", back_populates="assistant_cases", foreign_keys="Case.assistant_lawyer_id")
    execution_lawyer = relationship("User", back_populates="execution_cases", foreign_keys="Case.execution_lawyer_id")
    execution_assistant = relationship("User", back_populates="execution_assistant_cases",
                                       foreign_keys="Case.execution_assistant_id")
