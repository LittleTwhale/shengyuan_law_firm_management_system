# utils/error_analyzer.py
"""
错误分析引擎（Error Analyzer）

当 FastAPI 捕获到未处理的异常时，该模块负责：
1. 同步阶段（prepare_error_analysis）：提取错误信息、脱敏、去重、创建 DB 记录
2. 异步阶段（run_analysis）：调用 DeepSeek API 分析错误、更新 DB 结果

两阶段设计的目的：
- 500 响应可以立即返回 analysis_id 给前端
- 前端拿到 ID 后轮询分析结果，完成后弹窗通知用户

与 llm_client.py 的关系：
- llm_client.py 用于"案件智能分析"业务场景
- 本模块专注于"服务器错误诊断"场景，两者独立
"""
import hashlib
import json
import logging
import re
import traceback
from typing import Optional

import httpx
from fastapi import Request
from sqlalchemy.orm import Session

from ..core.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
from ..crud.error_analysis_crud import (
    create_error_analysis,
    find_recent_analysis_by_fingerprint,
    get_analysis,
    update_analysis_result,
    mark_analysis_failed,
    mark_analysis_processing,
)
from ..database.database import SessionLocal

logger = logging.getLogger("shengyuan_app.error_analyzer")

# DeepSeek 模型配置
# 与 llm_client.py 保持一致，使用 deepseek-v4-flash 模型
MODEL_NAME = "deepseek-v4-flash"
REQUEST_TIMEOUT = 60  # 错误分析不需要像案件分析那么长超时
MAX_TOKENS = 2000     # 面向用户的操作指导

# ─── 敏感信息脱敏规则 ─────────────────────────────────────────

SENSITIVE_PATTERNS = [
    # DeepSeek / OpenAI API Key
    (re.compile(r'sk-[a-zA-Z0-9]{20,}', re.IGNORECASE), 'sk-***'),
    # 各种 Token
    (re.compile(r'[Bb]earer\s+[a-zA-Z0-9\-_.]{20,}', re.IGNORECASE), 'Bearer ***'),
    # JWT-like tokens
    (re.compile(r'eyJ[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+'), '***jwt***'),
    # 密码字段 (JSON) — 用 lambda 保留原字段名的大小写
    (re.compile(r'"(password|passwd|pwd|secret)"\s*:\s*"[^"]*"', re.IGNORECASE), lambda m: f'"{m.group(1)}":"***"'),
    # 身份证号
    (re.compile(r'\b\d{17}[\dXx]\b'), '***id***'),
    # 手机号
    (re.compile(r'\b1[3-9]\d{9}\b'), '***phone***'),
]


def sanitize_text(text: str) -> str:
    """对文本中的敏感信息进行脱敏处理"""
    if not text:
        return text
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def sanitize_request_body(body: Optional[str], max_length: int = 2000) -> Optional[str]:
    """脱敏并截断请求体"""
    if not body:
        return None
    sanitized = sanitize_text(body)
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "\n... [截断]"
    return sanitized


# ─── 错误指纹生成 ─────────────────────────────────────────────

def generate_fingerprint(error_type: str, error_message: str, traceback_summary: str) -> str:
    """
    生成错误指纹，用于判断是否同一错误的重复出现。
    将异常类型 + 关键异常消息 + 堆栈前 500 字做 MD5。
    """
    raw = f"{error_type}|{error_message[:200]}|{traceback_summary[:500]}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


# ─── 提取错误信息 ─────────────────────────────────────────────

def extract_error_info(exc: Exception, request: Request) -> dict:
    """
    从异常对象和 Request 中提取结构化的错误信息
    """
    # 异常类型
    error_type = type(exc).__name__

    # 异常消息（截断）
    error_message = str(exc)[:1000] if str(exc) else "无异常消息"

    # 堆栈摘要
    tb_str = traceback.format_exc()
    traceback_summary = sanitize_text(tb_str[:3000]) if tb_str else None

    # 请求上下文
    request_method = request.method if request else None
    request_path = str(request.url.path) if request else None
    user_ip = (
        request.headers.get("X-Forwarded-For")
        or (request.client.host if request.client else None)
    )

    # 从 Authorization 头中提取用户名（不阻塞，不查库）
    user_accounts = None
    user_real_name = None
    try:
        # 由 middleware 已解析的用户信息，直接从 request.state 读取
        if hasattr(request.state, "user_accounts"):
            user_accounts = request.state.user_accounts
        if hasattr(request.state, "username"):
            user_real_name = request.state.username
    except Exception:
        pass

    # URL 查询参数（脱敏）
    query_params = None
    try:
        if request.query_params:
            params_dict = dict(request.query_params)
            query_params = json.dumps(sanitize_text(str(params_dict)), ensure_ascii=False)
    except Exception:
        pass

    # 请求体 — 注意：不能在异常处理器中再次读取 body（已消费）
    # 可以从 request.state 中获取（如果 middleware 存了的话）
    body_snippet = None
    try:
        if hasattr(request.state, "request_body"):
            body_snippet = sanitize_request_body(request.state.request_body)
    except Exception:
        pass

    return {
        "error_type": error_type,
        "error_message": sanitize_text(error_message),
        "traceback_summary": traceback_summary,
        "request_method": request_method,
        "request_path": request_path,
        "user_accounts": user_accounts,
        "user_real_name": user_real_name,
        "user_ip": user_ip,
        "request_query_params": query_params,
        "request_body_snippet": body_snippet,
        "analysis_status": "pending",
    }


# ─── 构建 DeepSeek Prompt ────────────────────────────────────

def build_analysis_prompt(error_info: dict) -> str:
    """
    构建发送给 DeepSeek 的 Prompt。
    面向终端用户，要求 AI 用通俗语言解释错误并给出操作指导。
    """
    prompt = f"""你是一个律师事务所管理系统（律所OA）的错误诊断助手。
用户在日常操作中遇到了以下错误，请帮助分析并指导用户如何正确操作。

### 分析规则

首先判断错误属于哪一类：

**A. 用户操作错误**（占大多数）—— 如输入格式不对、必填字段为空、数据重复、字段超长、权限不足、关联数据不存在等
→ 用通俗语言告诉用户哪里出错了、应该怎么做

**B. 系统错误**（占少数）—— 如代码 Bug、服务器配置问题、第三方服务异常等
→ 告知用户此问题需要技术人员处理，建议联系系统管理员

### 回复格式（Markdown，约 400-600 字）

**错误类型**：用户操作错误 / 系统错误

**问题说明**：用通俗的语言解释发生了什么，为什么会出错

**正确操作**：
- 用户操作错误时，列出 2-4 条具体的正确操作方法，包含必要的字段格式说明
- 系统错误时，说明"此问题需要技术人员处理，请联系系统管理员"，并简要说明可能原因

**提示**：可补充一条避免再次出错的注意事项

**技术参考**（面向开发/运维人员）：
- 结合堆栈摘要，简要指出可能涉及的后端代码模块、数据库约束或配置问题
- 给出 1-2 条技术层面的排查方向或修复思路
- 这部分约 100-150 字，可使用技术术语

---

### 错误信息

| 字段 | 值 |
|------|-----|
| 异常类型 | {error_info.get('error_type', 'N/A')} |
| 异常消息 | {error_info.get('error_message', 'N/A')} |
| 请求路径 | {error_info.get('request_path', 'N/A')} |

### 堆栈摘要（供判断错误类型参考）

```
{error_info.get('traceback_summary', '无')[:1500]}
```

请用中文回答。面向用户的部分保持通俗易懂，技术参考部分可使用专业术语。总长度约 400-600 字。"""
    return prompt


# ─── 调用 DeepSeek API ───────────────────────────────────────

async def call_deepseek_for_analysis(error_info: dict) -> str:
    """
    调用 DeepSeek Chat API 进行错误分析

    Returns:
        DeepSeek 返回的分析文本（Markdown 格式）

    Raises:
        ValueError: API Key 未配置
        ConnectionError: 网络连接失败
        RuntimeError: API 返回错误
    """
    if not DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY 未配置，请在 .env 中设置")

    prompt = build_analysis_prompt(error_info)

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": "你是一个律师事务所管理系统的错误诊断助手。你的任务分两部分：前半部分用通俗易懂的中文向普通用户解释错误原因和正确操作方法，优先判断是否为用户操作错误；最后附加一段简短的「技术参考」，面向开发人员指出可能涉及的代码模块或数据库约束，使用专业术语。回复使用 Markdown 格式，约 400-600 字。",
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": MAX_TOKENS,
        "temperature": 0.3,  # 低温度让输出更聚焦、更确定
    }

    api_url = f"{DEEPSEEK_BASE_URL.rstrip('/')}/v1/chat/completions"

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        for attempt in range(3):  # 最多重试 3 次
            try:
                response = await client.post(api_url, headers=headers, json=payload)

                if response.status_code == 429:
                    logger.warning("DeepSeek API 限流（第 %d/3 次），等待重试...", attempt + 1)
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
                    continue

                if response.status_code == 400:
                    err_body = response.text[:500]
                    logger.error("DeepSeek API 400 错误: %s", err_body)
                    raise RuntimeError(f"DeepSeek API 请求参数错误: {err_body}")

                response.raise_for_status()
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return content

            except httpx.TimeoutException:
                if attempt < 2:
                    import asyncio
                    logger.warning("DeepSeek API 超时（第 %d/3 次），重试...", attempt + 1)
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise ConnectionError("DeepSeek API 连接超时，请检查网络")
            except httpx.ConnectError:
                raise ConnectionError("无法连接到 DeepSeek API，请检查网络和 API 地址配置")
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (500, 502, 503, 504) and attempt < 2:
                    import asyncio
                    logger.warning("DeepSeek API %d（第 %d/3 次），重试...", e.response.status_code, attempt + 1)
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f"DeepSeek API HTTP {e.response.status_code}: {e.response.text[:300]}")

    raise RuntimeError("DeepSeek API 请求失败（已重试 3 次）")


# ─── 阶段一：同步准备 ─────────────────────────────────────────

def prepare_error_analysis(exc: Exception, request: Request) -> dict:
    """
    【同步阶段】在异常处理器中直接调用，不阻塞响应返回。

    职责：
    1. 提取并脱敏错误信息
    2. 生成错误指纹、检查去重
    3. 创建数据库记录（status=pending）
    4. 返回 analysis_id 等信息，供 500 响应使用

    Returns:
        {
            "analysis_id": int | None,
            "status": "pending" | "completed" | "failed",
            "error_type": str,
            "result": str | None,        # 仅去重命中时有值
            "is_duplicate": bool,
        }
    """
    db: Optional[Session] = None
    try:
        db = SessionLocal()

        # 1. 提取错误信息
        error_info = extract_error_info(exc, request)
        error_info["analysis_status"] = "pending"

        # 2. 生成指纹
        fingerprint = generate_fingerprint(
            error_info["error_type"],
            error_info["error_message"],
            error_info.get("traceback_summary") or "",
        )
        error_info["error_fingerprint"] = fingerprint

        # 3. 去重检查
        existing = find_recent_analysis_by_fingerprint(db, fingerprint, within_minutes=60)
        if existing:
            logger.info(
                "错误 [%s] 在 60 分钟内已有分析结果（ID=%d），直接复用",
                error_info["error_type"], existing.id,
            )
            return {
                "analysis_id": existing.id,
                "status": "completed",
                "error_type": existing.error_type,
                "result": existing.analysis_result,
                "is_duplicate": True,
            }

        # 4. 创建记录
        record = create_error_analysis(db, error_info)
        analysis_id = record.id
        logger.info(
            "创建错误分析记录 ID=%d, 类型=%s, 路径=%s",
            analysis_id, error_info["error_type"], error_info.get("request_path"),
        )

        return {
            "analysis_id": analysis_id,
            "status": "pending",
            "error_type": error_info["error_type"],
            "result": None,
            "is_duplicate": False,
        }

    except Exception as e:
        logger.error("准备错误分析记录失败: %s", e, exc_info=True)
        return {
            "analysis_id": None,
            "status": "failed",
            "error_type": None,
            "result": None,
            "is_duplicate": False,
        }
    finally:
        if db:
            try:
                db.close()
            except Exception:
                pass


# ─── 阶段二：异步分析 ─────────────────────────────────────────

async def run_analysis(analysis_id: int):
    """
    【异步阶段】由 asyncio.create_task 调度，不阻塞主请求。

    职责：
    1. 标记记录为 processing
    2. 调用 DeepSeek API 分析错误
    3. 更新分析结果到数据库
    """
    db: Optional[Session] = None
    try:
        db = SessionLocal()

        # 1. 标记处理中
        mark_analysis_processing(db, analysis_id)

        # 2. 读取记录，构建 error_info
        record = get_analysis(db, analysis_id)
        if not record:
            logger.error("分析记录 ID=%d 不存在，无法执行分析", analysis_id)
            return

        error_info = {
            "error_type": record.error_type,
            "error_message": record.error_message,
            "traceback_summary": record.traceback_summary,
            "request_method": record.request_method,
            "request_path": record.request_path,
        }

        # 3. 调用 DeepSeek
        logger.info("开始调用 DeepSeek 分析错误 ID=%d...", analysis_id)
        analysis_result = await call_deepseek_for_analysis(error_info)

        # 4. 存储结果
        update_analysis_result(db, analysis_id, analysis_result)
        logger.info("错误分析完成 ID=%d（%d 字符）", analysis_id, len(analysis_result))

    except Exception as e:
        logger.error("错误分析过程异常 ID=%d: %s", analysis_id, e, exc_info=True)
        try:
            mark_analysis_failed(db, analysis_id, str(e)[:500])
        except Exception:
            pass
    finally:
        if db:
            try:
                db.close()
            except Exception:
                pass
