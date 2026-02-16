# models/finance_model.py
from sqlalchemy import Column, Integer, String, DECIMAL, Date, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from ..database.database import Base


class CaseFinance(Base):
    """
    案件财务总表 (Snapshot)
    与 Case 表是一对一关系，用于记录该案件当前的财务全貌。
    """
    __tablename__ = "case_finances"

    id = Column(Integer, primary_key=True, index=True, comment="财务ID")
    case_id = Column(Integer, ForeignKey("cases.case_id"), unique=True, nullable=False, comment="关联案件ID")

    # 1. 合同约定
    contract_amount = Column(DECIMAL(15, 2), default=0, comment="合同规定金额")
    risk_agency_content = Column(Text, nullable=True, comment="风险代理约定内容")

    # 2. 实际发生 (这些字段可以通过流水表计算得出，也可以手动调整，作为冗余字段提高查询速度)
    final_contract_amount = Column(DECIMAL(15, 2), default=0, comment="合同最终收费金额")

    # 3. 结算状态 (汇总字段)
    total_invoiced_amount = Column(DECIMAL(15, 2), default=0, comment="累计已开票金额")
    total_received_amount = Column(DECIMAL(15, 2), default=0, comment="累计实收金额(进账)")
    total_refund_amount = Column(DECIMAL(15, 2), default=0, comment="累计退费金额")
    total_withdrawal_amount = Column(DECIMAL(15, 2), default=0, comment="累计律师领款金额")

    # 4. 计算字段 (通常由前端计算，存库是为了方便排序和筛选)
    # 未开票 = final_contract_amount - total_invoiced_amount
    uninvoiced_amount = Column(DECIMAL(15, 2), default=0, comment="未开票金额")
    # 未付 = final_contract_amount - total_received_amount
    unpaid_amount = Column(DECIMAL(15, 2), default=0, comment="未付金额(尾款)")

    remarks = Column(Text, nullable=True, comment="财务备注")

    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now(), comment="更新时间")

    # 关系
    case = relationship("Case", back_populates="finance")
    records = relationship("FinancialRecord", back_populates="finance", cascade="all, delete-orphan")
    invoices = relationship("InvoiceRecord", back_populates="finance", cascade="all, delete-orphan")
    withdrawals = relationship("LawyerWithdrawal", back_populates="finance", cascade="all, delete-orphan")


class FinancialRecord(Base):
    """
    财务收支流水表 (Transaction)
    记录每一笔具体的进账或退款，用于按时间段统计业绩。
    """
    __tablename__ = "financial_records"

    id = Column(Integer, primary_key=True, index=True)
    finance_id = Column(Integer, ForeignKey("case_finances.id"), nullable=False, comment="关联财务总表ID")

    # 记录类型
    record_type = Column(String(20), default="income", comment="类型: income(收款), refund(退费)")

    amount = Column(DECIMAL(15, 2), nullable=False, comment="金额")
    transaction_date = Column(Date, nullable=False, comment="发生日期(到账日)")
    payer = Column(String(100), nullable=True, comment="付款人/收款人")
    payment_method = Column(String(50), nullable=True, comment="支付方式(转账/现金/支票)")

    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="登记人/操作员ID")
    remarks = Column(String(255), nullable=True, comment="备注")

    created_at = Column(DateTime, server_default=func.now())

    # 关系
    finance = relationship("CaseFinance", back_populates="records")
    operator = relationship("User")


class InvoiceRecord(Base):
    """
    发票开具记录表
    用于按时间段统计税务开票情况。
    """
    __tablename__ = "invoice_records"

    id = Column(Integer, primary_key=True, index=True)
    finance_id = Column(Integer, ForeignKey("case_finances.id"), nullable=False, comment="关联财务总表ID")

    invoice_amount = Column(DECIMAL(15, 2), nullable=False, comment="开票金额")
    invoice_date = Column(Date, nullable=False, comment="开票日期")
    invoice_number = Column(String(100), nullable=True, comment="发票号码")
    invoice_title = Column(String(200), nullable=True, comment="发票抬头")
    tax_number = Column(String(100), nullable=True, comment="税号")

    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="开票经办人ID")
    remarks = Column(String(255), nullable=True, comment="备注")

    created_at = Column(DateTime, server_default=func.now())

    # 关系
    finance = relationship("CaseFinance", back_populates="invoices")
    operator = relationship("User")


class LawyerWithdrawal(Base):
    """
    律师领款记录表
    记录案件的主办、承办或其他律师的提成/领款明细。
    """
    __tablename__ = "lawyer_withdrawals"

    id = Column(Integer, primary_key=True, index=True)
    finance_id = Column(Integer, ForeignKey("case_finances.id"), nullable=False, comment="关联财务总表ID")

    # 领款律师 (可能是主办，也可能是其他律师)
    lawyer_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="领款律师ID")

    amount = Column(DECIMAL(15, 2), nullable=False, comment="领款金额")
    withdrawal_date = Column(Date, nullable=False, comment="领款日期")

    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="操作员ID")
    remarks = Column(String(255), nullable=True, comment="备注")

    created_at = Column(DateTime, server_default=func.now())

    # 关系
    finance = relationship("CaseFinance", back_populates="withdrawals")

    # 指明外键关系，防止多个 User 外键冲突
    lawyer = relationship("User", foreign_keys="LawyerWithdrawal.lawyer_id")
    operator = relationship("User", foreign_keys="LawyerWithdrawal.operator_id")