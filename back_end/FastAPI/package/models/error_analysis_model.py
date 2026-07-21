# models/error_analysis_model.py
"""
错误分析记录模型（Error Analysis Model）

当服务器未捕获的异常触发时，系统自动将错误信息发送至 DeepSeek API
进行分析，分析结果存入此表，供用户后续查阅。
"""
from sqlalchemy import (
    Boolean, Column, Integer, String, Text, DateTime, TIMESTAMP,
    func, Enum as SAEnum,
)
from ..database.database import Base


class ErrorAnalysis(Base):
    """服务器错误分析记录表"""
    __tablename__ = "error_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── 错误基本信息 ──
    error_type = Column(
        String(120), nullable=False, index=True,
        comment="异常类型名，如 ValueError、IntegrityError",
    )
    error_message = Column(
        String(1000), nullable=False,
        comment="异常消息（截断至 1000 字符）",
    )
    traceback_summary = Column(
        Text, nullable=True,
        comment="关键堆栈摘要（前 3000 字符）",
    )

    # ── 请求上下文 ──
    request_method = Column(
        String(10), nullable=True,
        comment="HTTP 请求方法: GET / POST / PUT / DELETE",
    )
    request_path = Column(
        String(500), nullable=True,
        comment="请求路径，如 /api/cases/123",
    )
    user_accounts = Column(
        String(100), nullable=True, index=True,
        comment="触发错误的用户账号（accounts 字段），匿名用户为 NULL",
    )
    user_real_name = Column(
        String(50), nullable=True,
        comment="用户的真实姓名（real_name），便于前端显示",
    )
    user_ip = Column(
        String(45), nullable=True,
        comment="客户端 IP 地址（支持 IPv6 长度）",
    )
    request_query_params = Column(
        Text, nullable=True,
        comment="URL 查询参数（JSON 格式，已脱敏）",
    )
    request_body_snippet = Column(
        Text, nullable=True,
        comment="请求体片段（截断至 2000 字符，已脱敏）",
    )

    # ── 分析结果 ──
    analysis_result = Column(
        Text, nullable=True,
        comment="DeepSeek 返回的错误分析 + 解决方案（Markdown 格式）",
    )
    analysis_status = Column(
        SAEnum(
            "pending", "processing", "completed", "failed",
            name="analysis_status_enum",
        ),
        nullable=False, default="pending", index=True,
        comment="分析状态: pending=排队, processing=分析中, completed=完成, failed=失败",
    )
    analysis_error = Column(
        String(500), nullable=True,
        comment="分析失败时的错误信息（如 API 调用失败原因）",
    )

    # ── 通知状态 ──
    notified = Column(
        Boolean, nullable=False, default=False, index=True,
        comment="是否已通知触发用户（用于前台轮询兜底，覆盖非 500 场景）",
    )

    # ── 去重与时间 ──
    error_fingerprint = Column(
        String(64), nullable=True, index=True,
        comment="错误指纹（MD5），用于短时间内相同错误去重",
    )

    created_at = Column(
        TIMESTAMP, server_default=func.now(), nullable=False,
        comment="记录创建时间",
    )
    analyzed_at = Column(
        DateTime, nullable=True,
        comment="DeepSeek 分析完成时间",
    )
