"""
DeepSeek LLM 客户端
封装对 DeepSeek Chat API 的异步调用，用于案件智能分析
包含 RAG 法律知识库检索集成
"""
import asyncio
import logging
import json
import re
from typing import Optional, AsyncGenerator

import httpx
import meilisearch

from ..core.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    MEILI_URL,
    MEILI_MASTER_KEY,
)
from ..utils.llm_prompts import (
    SYSTEM_PROMPT,
    CHAT_SYSTEM_PROMPT,
    EXCEL_ERROR_DIAGNOSE_PROMPT,
    DATE_LABELS,
    BANK_FIELDS,
    FINANCE_FIELDS,
)

# 使用 shengyuan_app 作为父 logger，确保日志进入系统统一的日志系统
logger = logging.getLogger("shengyuan_app.llm_client")

# DeepSeek 模型名
MODEL_NAME = "deepseek-v4-flash"


# 请求超时（秒）— 长文本分析可能需要较长时间
REQUEST_TIMEOUT = 120

# 单次请求最大 token 数
MAX_TOKENS = 100000


# 系统提示词从 llm_prompts.py 导入

# 对话单次回复最大 token（追问回复不需太长）
CHAT_MAX_TOKENS = 10000

# 对话系统提示词从 llm_prompts.py 导入

# =================================================================
#  重试与并发控制
# =================================================================

# 全局信号量，限制同时进行的 LLM 请求数（防止 API 429 + 控制成本）
_LLM_SEMAPHORE = asyncio.Semaphore(3)


async def _retry_with_backoff(fn, *args, max_retries=3, base_delay=1.0, **kwargs):
    """
    指数退避重试，仅对可重试的错误（超时、429、5xx）重试
    4xx 客户端错误（除 429 外）不重试
    """
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return await fn(*args, **kwargs)
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            last_error = e
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    "API 调用失败（第 %d/%d 次），%.1f 秒后重试: %s",
                    attempt + 1, max_retries + 1, delay, e,
                )
                await asyncio.sleep(delay)
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    "API HTTP %d（第 %d/%d 次），%.1f 秒后重试",
                    e.response.status_code, attempt + 1, max_retries + 1, delay,
                )
                await asyncio.sleep(delay)
            else:
                raise  # 不重试 4xx 等客户端错误
    raise last_error  # 所有重试均失败


async def _post_llm_request(url: str, headers: dict, payload: dict) -> httpx.Response:
    """执行一次 LLM API 的 HTTP POST 请求（用于重试包装）"""
    async with httpx.AsyncClient(timeout=httpx.Timeout(REQUEST_TIMEOUT, connect=30.0)) as client:
        return await client.post(url, headers=headers, json=payload)


# =================================================================
#  RAG 法律知识库检索
# =================================================================

LEGAL_INDEX = "legal_provisions"

# LLM 关键词生成超时（短任务，不需要和主分析一样长）
_KEYWORD_TIMEOUT = 20


async def _generate_search_keywords(case_data: dict) -> list[str]:
    """
    让 DeepSeek 根据案件数据生成检索法律知识库的关键词短语

    返回关键词列表（JSON 字符串数组），用于多路并行检索。
    失败时返回空列表，调用方自动降级到基础检索（不阻塞主流程）。
    """
    info = case_data.get("case_info", {})
    bank = case_data.get("bank_case", {})

    # 构造精简案件摘要（控制在 400 字以内，快速 + 省 token）
    summary_parts = [
        f"案由：{info.get('cause', '未记录')}",
        f"案件类别：{info.get('case_category', '未记录')}",
    ]
    details = info.get('details', '')
    if details and len(details) > 5:
        summary_parts.append(f"案件详情：{details[:300]}")
    if bank:
        if bank.get('loan_type'):
            summary_parts.append(f"贷款类型：{bank['loan_type']}")
        if bank.get('litigation_target_amount'):
            summary_parts.append(f"标的金额：{bank['litigation_target_amount']}")

    summary = "\n".join(summary_parts)

    prompt = (
        "你是一位法律检索专家。请根据以下案件信息，生成 3-6 个检索关键词短语，"
        "用于在法律条文知识库中检索最相关的法条。\n\n"
        "要求：\n"
        "1. 每个关键词短语应覆盖一个独立的法律检索维度\n"
        "2. 覆盖实体法、程序法、司法解释等多个角度\n"
        "3. 考虑可能的时效、担保、违约责任等子问题\n"
        "4. 每个关键词短语 2-8 个汉字，不要过长也不要过短\n"
        "5. 直接输出 JSON 字符串数组，不要其他内容\n\n"
        f"案件信息：\n{summary}"
    )

    messages = [
        {
            "role": "system",
            "content": "你是一个法律检索关键词生成专家。只输出 JSON 数组，不要其他任何内容。",
        },
        {"role": "user", "content": prompt},
    ]

    url = f"{DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.1,  # 低温度确保确定性输出
        "max_tokens": 300,   # 关键词很短，不需要很多 token
        "stream": False,
    }

    try:
        async with _LLM_SEMAPHORE:
            # 关键词生成用较短超时，失败不阻塞
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(_KEYWORD_TIMEOUT, connect=10.0)
            ) as client:
                response = await _retry_with_backoff(
                    lambda: client.post(url, headers=headers, json=payload),
                    max_retries=1,  # 只重试 1 次，快速失败
                )

        content = response.json()["choices"][0]["message"]["content"]

        # 用正则提取 JSON 数组（防御 LLM 输出多余文字）
        json_match = re.search(r'\[.*?\]', content, re.DOTALL)
        if json_match:
            keywords = json.loads(json_match.group())
            if isinstance(keywords, list) and len(keywords) > 0:
                # 过滤：只保留 2-20 字的有效关键词
                keywords = [
                    kw.strip() for kw in keywords
                    if kw.strip() and 2 <= len(kw.strip()) <= 20
                ]
                if keywords:
                    logger.info("LLM 生成检索关键词: %s", keywords)
                    return keywords[:8]  # 最多 8 个

        logger.warning("LLM 关键词格式异常，原始输出: %s", content[:200])
    except Exception as e:
        logger.warning("LLM 关键词生成失败（降级到基础检索）: %s", e)

    return []  # 失败返回空列表


async def search_relevant_provisions(
    case_data: dict,
    top_k: int = 10,
) -> list[dict]:
    """
    根据案件信息在 Meilisearch 法律知识库中检索相关条文（RAG 第一步）

    采用两路并行检索策略：
    1. 基础检索：用案由 + 案件类别直搜（快速保底，数十毫秒完成）
    2. LLM 关键词扩展：让 DeepSeek 根据案件详情生成多维度检索词
    两路结果合并去重后返回 top-k，任一环节失败自动降级。
    """
    info = case_data.get("case_info", {})
    cause = info.get("cause", "")
    category = info.get("case_category", "")

    query_parts = []
    if cause:
        query_parts.append(cause)
    if category:
        query_parts.append(category)

    query = " ".join(query_parts).strip()
    if not query:
        logger.info("RAG 检索：案件信息不足，跳过")
        return []

    logger.info("RAG 检索：案由=%s, 类别=%s", cause, category)

    try:
        client = meilisearch.Client(MEILI_URL, MEILI_MASTER_KEY)
        index = client.index(LEGAL_INDEX)

        # ========== 第一路：基础检索（保底）==========
        basic_result = index.search(query, {
            "limit": top_k,
            "attributesToRetrieve": ["id", "law_name", "article_number", "chapter", "content", "law_category"],
        })
        basic_hits = basic_result.get("hits", [])

        # ========== 第二路：LLM 关键词扩展（与基础检索并行）==========
        llm_keywords = await _generate_search_keywords(case_data)

        extra_hits = []
        if llm_keywords:
            # 用每个 LLM 关键词独立检索（同步调用，Meilisearch SDK v0.41 的 search() 非异步）
            for kw in llm_keywords:
                r = index.search(kw, {
                    "limit": 3,
                    "attributesToRetrieve": ["id", "law_name", "article_number", "chapter", "content", "law_category"],
                })
                extra_hits.extend(r.get("hits", []))

        # ========== 合并去重：按文档 ID 去重，保留最早出现（基础优先）==========
        seen_ids = set()
        merged = []

        for hit in basic_hits:
            raw_id = hit.get("id")
            if raw_id is None:
                continue
            # 防御：某些 SDK 版本可能返回非字符串 ID
            doc_id = str(raw_id) if not isinstance(raw_id, str) else raw_id
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                merged.append(hit)

        for hit in extra_hits:
            raw_id = hit.get("id")
            if raw_id is None:
                continue
            doc_id = str(raw_id) if not isinstance(raw_id, str) else raw_id
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                merged.append(hit)

        # 按相关性分数降序排列
        merged.sort(key=lambda x: -x.get("_score", 0))

        # 取 top_k
        provisions = []
        for hit in merged[:top_k]:
            provisions.append({
                "law_name": hit.get("law_name"),
                "article_number": hit.get("article_number"),
                "chapter": hit.get("chapter"),
                "content": hit.get("content"),
                "law_category": hit.get("law_category"),
            })

        logger.info("RAG 检索完成：基础命中 %d 条，LLM 扩展命中 %d 条，合并去重后 %d 条，最终返回 top-%d",
                    len(basic_hits), len(extra_hits), len(merged), top_k)
        for p in provisions:
            logger.info("  - %s %s: %s...", p["law_name"], p["article_number"], p["content"][:60])

        return provisions

    except Exception as e:
        logger.warning("RAG 检索失败（不阻塞主流程）: %s", e)
        return []


def _build_user_message(
    case_data: dict,
    extra_texts: Optional[list[str]] = None,
    relevant_provisions: Optional[list[dict]] = None,
) -> str:
    """将结构化的案件数据拼装为用户消息文本，可选注入 RAG 检索到的法条"""
    parts = []

    # ====== 注入当前时间，避免模型"瞎猜"时间 ======
    from datetime import datetime
    current_date = datetime.now().strftime("%Y年%m月%d日")
    parts.append("【系统环境信息】当前真实日期是：" + current_date + "。请务必以此日期为基准来计算时效、期限和案件紧迫程度，绝不可自行猜测当前时间。")

    # ====== 案件基本信息 ======
    info = case_data.get("case_info", {})
    parts.append("## 案件基本信息")
    parts.append(f"- 案号：{info.get('case_number', '未记录')}")
    parts.append(f"- 案件类别：{info.get('case_category', '未记录')}")
    parts.append(f"- 案由：{info.get('cause', '未记录')}")
    parts.append(f"- 审理法院：{info.get('court', '未记录')}")
    parts.append(f"- 案件地点：{info.get('location', '未记录')}")
    parts.append(f"- 代理权限：{info.get('agency_power', '未记录')}")
    parts.append(f"- 介入阶段：{info.get('stage', '未记录')}")
    parts.append(f"- 案件详情：{info.get('details', '未记录')}")

    # ====== 日期信息 ======
    dates = {k: v for k, v in info.items() if k.endswith("_date") and v}
    if dates:
        parts.append("\n## 系统记录的日期节点")
        for field, label in DATE_LABELS.items():
            val = dates.get(field)
            if val:
                parts.append(f"- {label}：{val}")

    # ====== 当事人信息（已过滤敏感字段） ======
    parties = case_data.get("parties", [])
    if parties:
        parts.append("\n## 当事人信息")
        for p in parties:
            parts.append(f"- {p.get('party_type', '未知')}：{p.get('name', '未记录')}")
            if p.get("legal_representative"):
                parts.append(f"  - 法定代表人：{p['legal_representative']}")

    # ====== 银行案件专属数据 ======
    bank = case_data.get("bank_case")
    if bank and any(v for v in bank.values()):
        parts.append("\n## 银行案件数据")
        for field, label in BANK_FIELDS.items():
            val = bank.get(field)
            if val is not None and val != "" and val != 0:
                parts.append(f"- {label}：{val}")

    # ====== 财务信息 ======
    finance = case_data.get("finance")
    if finance and any(v for v in finance.values()):
        parts.append("\n## 案件财务信息")
        for field, label in FINANCE_FIELDS.items():
            val = finance.get(field)
            if val is not None and val != 0:
                parts.append(f"- {label}：{val}")

    # ====== 卷宗与 OCR 内容 ======
    volumes = case_data.get("volumes", [])
    if volumes:
        parts.append("\n## 案件卷宗材料")
        for v in volumes:
            parts.append(f"\n### 卷册：{v.get('name', '未命名')}")
            files = v.get("files", [])
            for f in files:
                parts.append(f"\n#### 文件：{f.get('file_name', '未命名')}")
                parts.append(f"- 分类：{f.get('category', '其他')}")
                ocr = f.get("ocr_content", "")
                if ocr and len(ocr.strip()) > 20:
                    # deepseek-v4 上下文窗口极大，可传入更多内容
                    truncated = ocr.strip()[:8000]
                    parts.append(f"- OCR 内容摘要（前 8000 字）：\n```\n{truncated}\n```")
                else:
                    parts.append("- OCR 内容：无有效文本")

    # ====== 用户额外上传的文件文本 ======
    if extra_texts:
        parts.append("\n## 用户额外上传的文件")
        for i, text in enumerate(extra_texts):
            if text and len(text.strip()) > 20:
                truncated = text.strip()[:8000]
                parts.append(f"\n### 额外文件 {i+1} 内容（前 8000 字）：\n```\n{truncated}\n```")

    # ====== RAG 知识库检索到的相关法律条文 ======
    if relevant_provisions:
        parts.append("\n## 知识库检索到的相关法律条文（以下法条来自法律知识库，请结合案件实际情况选择性引用）")
        for i, p in enumerate(relevant_provisions):
            parts.append(
                f"\n### 参考法条 {i+1}：《{p['law_name']}》{p['article_number']}"
                f"\n- 所属章节：{p.get('chapter', '未分类')}"
                f"\n- 条文原文：\n> {p['content']}"
            )

    return "\n".join(parts)


def _build_brief_context(case_data: dict) -> str:
    """
    构建精简版案件摘要（用于追问对话，替代完整的 _build_user_message）
    目标：从 5000+ 字压缩到 800 字以内，仅保留核心要素
    """
    info = case_data.get("case_info", {})
    brief_parts = []

    brief_parts.append(f"案号：{info.get('case_number', '未记录')}")
    brief_parts.append(f"案件类别：{info.get('case_category', '未记录')}")
    brief_parts.append(f"案由：{info.get('cause', '未记录')}")
    brief_parts.append(f"审理法院：{info.get('court', '未记录')}")

    # 关键日期
    key_dates = []
    for field, label in DATE_LABELS.items():
        val = info.get(field)
        if val:
            key_dates.append(f"{label}={val}")
    if key_dates:
        brief_parts.append("关键日期：" + "; ".join(key_dates))

    # 当事人（仅名称和类型）
    parties = case_data.get("parties", [])
    if parties:
        party_strs = [f"{p.get('party_type', '未知')}: {p.get('name', '未记录')}" for p in parties]
        brief_parts.append("当事人：" + " | ".join(party_strs))

    # 标的金额（银行案件）
    bank = case_data.get("bank_case")
    if bank and bank.get("litigation_target_amount"):
        brief_parts.append(f"标的金额：{bank['litigation_target_amount']}")

    # 卷宗概要（仅统计数量）
    volumes = case_data.get("volumes", [])
    total_files = sum(len(v.get("files", [])) for v in volumes)
    if total_files > 0:
        brief_parts.append(f"卷宗材料：{len(volumes)} 册共 {total_files} 个文件")

    return "\n".join(brief_parts)


def _build_rag_provisions_text(provisions: list[dict]) -> str:
    """将 RAG 检索到的法律条文格式化为可注入对话的文本"""
    if not provisions:
        return ""
    lines = ["\n## 知识库检索到的相关法律条文（以下法条来自法律知识库，请结合案件实际情况选择性引用）"]
    for i, p in enumerate(provisions):
        lines.append(
            f"\n### 参考法条 {i+1}：《{p['law_name']}》{p['article_number']}"
            f"\n- 所属章节：{p.get('chapter', '未分类')}"
            f"\n- 条文原文：\n> {p['content']}"
        )
    return "\n".join(lines)


async def analyze_case(
    case_data: dict,
    extra_texts: Optional[list[str]] = None,
    relevant_provisions: Optional[list[dict]] = None,
    model: str = MODEL_NAME,
    max_tokens: int = MAX_TOKENS,
    temperature: float = 0.5,
) -> str:
    """
    调用 DeepSeek API 对案件进行智能分析

    Args:
        case_data: 聚合后的案件数据字典
        extra_texts: 用户额外上传文件的 OCR 文本列表
        relevant_provisions: RAG 检索到的相关法律条文（可选）
        model: 模型名称
        max_tokens: 最大输出 token 数
        temperature: 生成温度（越低越确定，0.5 适中）

    Returns:
        Markdown 格式的分析报告
    """
    if not DEEPSEEK_API_KEY:
        raise ValueError(
            "DeepSeek API Key 未配置，请在 .env 文件中设置 DEEPSEEK_API_KEY"
        )

    # 构建消息
    user_message = _build_user_message(case_data, extra_texts, relevant_provisions)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    # 构建请求
    url = f"{DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
        # 启用联网搜索，确保法律条文和典型案例的准确性与时效性
        "enable_search": True,
    }

    logger.info(
        "调用 DeepSeek API 分析案件（模型: %s, 案由: %s, 当事人: %d 人, 卷宗文件: %d 个）",
        model,
        case_data.get("case_info", {}).get("cause", "未知"),
        len(case_data.get("parties", [])),
        sum(
            len(v.get("files", []))
            for v in case_data.get("volumes", [])
        ),
    )

    try:
        async with _LLM_SEMAPHORE:
            response = await _retry_with_backoff(_post_llm_request, url, headers, payload)
    except httpx.TimeoutException:
        logger.error("DeepSeek API 请求超时（%d秒）", REQUEST_TIMEOUT)
        raise RuntimeError(
            f"DeepSeek API 请求超时（{REQUEST_TIMEOUT}秒），请检查网络连接或稍后重试"
        )
    except httpx.ConnectError:
        logger.error("无法连接到 DeepSeek API（%s）", DEEPSEEK_BASE_URL)
        raise ConnectionError(
            f"无法连接到 DeepSeek API（{DEEPSEEK_BASE_URL}），请检查网络连接"
        )
    except httpx.HTTPStatusError as e:
        logger.error("DeepSeek API HTTP 错误: %d, 响应: %s", e.response.status_code, e.response.text[:300])
        raise RuntimeError(f"DeepSeek API 返回 HTTP {e.response.status_code}，请查看日志获取详细信息")

    # 记录 API 原始响应状态码（便于排查）
    logger.info("DeepSeek API 原始响应状态码: %d", response.status_code)

    if response.status_code == 401:
        logger.error("DeepSeek API 认证失败, 响应: %s", response.text[:200])
        raise ValueError("DeepSeek API 认证失败，请检查 DEEPSEEK_API_KEY 是否正确")
    if response.status_code == 429:
        logger.error("DeepSeek API Rate Limit 触发")
        raise RuntimeError("DeepSeek API 请求过于频繁（Rate Limit），请稍后重试")
    if response.status_code == 400:
        err_body = response.text[:500]
        logger.error("DeepSeek API 400 错误: %s", err_body)
        raise RuntimeError(f"DeepSeek API 请求参数错误: {err_body}")

    response.raise_for_status()

    result = response.json()
    content = result["choices"][0]["message"]["content"]
    usage = result.get("usage", {})
    logger.info(
        "DeepSeek API 响应成功（输入 %d tokens, 输出 %d tokens）",
        usage.get("prompt_tokens", 0),
        usage.get("completion_tokens", 0),
    )

    return content.strip()


async def analyze_case_stream(
    case_data: dict,
    extra_texts: Optional[list[str]] = None,
    relevant_provisions: Optional[list[dict]] = None,
    model: str = MODEL_NAME,
    max_tokens: int = MAX_TOKENS,
    temperature: float = 0.5,
) -> AsyncGenerator[str, None]:
    """
    流式调用 DeepSeek API 对案件进行智能分析
    逐块 yield 出 Markdown 文本增量，前端可实时展示

    Args:
        case_data: 聚合后的案件数据字典
        extra_texts: 用户额外上传文件的 OCR 文本列表
        relevant_provisions: RAG 检索到的相关法律条文（可选）
        model: 模型名称
        max_tokens: 最大输出 token 数
        temperature: 生成温度

    Yields:
        SSE 格式的文本块，格式为 "data: {...}\n\n"

    Raises:
        ValueError: API Key 未配置
    """
    if not DEEPSEEK_API_KEY:
        raise ValueError("DeepSeek API Key 未配置，请在 .env 文件中设置 DEEPSEEK_API_KEY")

    # 构建消息（与 analyze_case 完全一致）
    user_message = _build_user_message(case_data, extra_texts, relevant_provisions)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    url = f"{DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
        "enable_search": True,
    }

    logger.info(
        "流式调用 DeepSeek API 分析案件（模型: %s, 案由: %s, 当事人: %d 人, 卷宗文件: %d 个）",
        model,
        case_data.get("case_info", {}).get("cause", "未知"),
        len(case_data.get("parties", [])),
        sum(len(v.get("files", [])) for v in case_data.get("volumes", [])),
    )

    try:
        async with _LLM_SEMAPHORE:
            # 流式重试：只在建立连接前重试，流开始后不重试
            async with httpx.AsyncClient(timeout=httpx.Timeout(REQUEST_TIMEOUT, connect=30.0)) as client:
                response = await _retry_with_backoff(
                    lambda: client.send(
                        client.build_request("POST", url, headers=headers, json=payload)
                    )
                )
                response.raise_for_status()

                # 读取 SSE 流
                buffer = ""
                token_count_in = 0
                token_count_out = 0

                async for raw_line in response.aiter_lines():
                    line = raw_line.strip()

                    # 跳过空行
                    if not line:
                        continue
                    # 跳过 SSE 注释
                    if line.startswith(": "):
                        continue
                    # 解析 data: 行
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                        except json.JSONDecodeError:
                            logger.warning("SSE 解析失败: %s", data_str[:100])
                            continue

                        # 提取 usage（最后一条 chunk 可能有）
                        usage = chunk.get("usage")
                        if usage:
                            token_count_in = usage.get("prompt_tokens", 0)
                            token_count_out = usage.get("completion_tokens", 0)

                        # 提取 delta.content
                        choices = chunk.get("choices", [])
                        if choices and len(choices) > 0:
                            delta = choices[0].get("delta", {})
                            content_delta = delta.get("content", "")
                            if content_delta:
                                yield content_delta

        logger.info(
            "流式分析完成（输入 %d tokens, 输出 %d tokens）",
            token_count_in,
            token_count_out,
        )

    except httpx.TimeoutException:
        logger.error("DeepSeek API 流式请求超时（%d秒）", REQUEST_TIMEOUT)
        raise RuntimeError(f"DeepSeek API 请求超时（{REQUEST_TIMEOUT}秒），请检查网络连接或稍后重试")
    except httpx.ConnectError:
        logger.error("无法连接到 DeepSeek API（%s）", DEEPSEEK_BASE_URL)
        raise ConnectionError(f"无法连接到 DeepSeek API（{DEEPSEEK_BASE_URL}），请检查网络连接")
    except httpx.HTTPStatusError as e:
        logger.error("DeepSeek API HTTP 错误: %d", e.response.status_code)
        raise RuntimeError(f"DeepSeek API 返回 HTTP {e.response.status_code}，请查看日志获取详细信息")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error("DeepSeek API 流式响应解析失败: %s", e)
        raise RuntimeError(f"DeepSeek API 响应解析失败: {e}")


async def chat_about_case(
    case_data: dict,
    report_markdown: str,
    chat_history: list[dict],
    user_message: str,
    relevant_provisions: Optional[list[dict]] = None,
    model: str = MODEL_NAME,
    max_tokens: int = CHAT_MAX_TOKENS,
    temperature: float = 0.7,
) -> str:
    """
    基于已生成的案件分析报告进行多轮对话追问

    Args:
        case_data: 聚合后的案件数据字典
        report_markdown: 之前生成的分析报告全文
        chat_history: 对话历史 [{"role": "user"|"assistant", "content": "..."}]
        user_message: 用户当前追问内容
        relevant_provisions: RAG 检索到的相关法律条文（可选）
        model: 模型名称
        max_tokens: 最大输出 token 数（对话回复较短）
        temperature: 生成温度（对话可稍高，更自然）

    Returns:
        Markdown 格式的追问回复
    """
    if not DEEPSEEK_API_KEY:
        raise ValueError("DeepSeek API Key 未配置")

    # 构建精简版案件摘要（替代完整数据，大幅节省 token）
    case_brief = _build_brief_context(case_data)
    report_brief = report_markdown[:3000] if len(report_markdown) > 3000 else report_markdown

    # RAG 法条文本
    rag_text = _build_rag_provisions_text(relevant_provisions) if relevant_provisions else ""

    # 组装消息列表
    messages = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"以下是一起案件的摘要和已生成的分析报告（开头部分），请仔细阅读：\n\n"
                       f"=== 案件摘要 ===\n{case_brief}\n\n"
                       f"=== 报告摘要 ===\n{report_brief}"
                       f"{rag_text}",
        },
        {
            "role": "assistant",
            "content": "我已仔细阅读案件摘要和分析报告，了解了案件全貌。请提出您的追问，我会基于已有信息提供专业分析。",
        },
    ]

    # 追加对话历史（限制最近 10 轮，防止上下文过长）
    for msg in chat_history[-20:]:  # 最多 20 条（10 轮对话）
        messages.append(msg)

    # 追加当前用户问题
    messages.append({"role": "user", "content": user_message})

    # 构建请求
    url = f"{DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
        "enable_search": True,
    }

    logger.info("DeepSeek 对话追问（历史 %d 轮，当前问题: %s...）",
                len(chat_history) // 2, user_message[:60])

    try:
        async with _LLM_SEMAPHORE:
            response = await _retry_with_backoff(_post_llm_request, url, headers, payload)
    except httpx.TimeoutException:
        logger.error("DeepSeek 对话 API 请求超时")
        raise RuntimeError(f"DeepSeek API 请求超时（{REQUEST_TIMEOUT}秒），请稍后重试")
    except httpx.ConnectError:
        logger.error("无法连接到 DeepSeek API")
        raise ConnectionError(f"无法连接到 DeepSeek API，请检查网络连接")
    except httpx.HTTPStatusError as e:
        logger.error("DeepSeek 对话 HTTP 错误: %d", e.response.status_code)
        raise RuntimeError(f"DeepSeek API 返回 HTTP {e.response.status_code}")

    logger.info("DeepSeek 对话 API 响应状态码: %d", response.status_code)

    if response.status_code == 400:
        err_body = response.text[:500]
        logger.error("DeepSeek 对话 API 400 错误: %s", err_body)
        raise RuntimeError(f"DeepSeek API 请求参数错误: {err_body}")
    if response.status_code == 401:
        raise ValueError("DeepSeek API 认证失败")
    if response.status_code == 429:
        raise RuntimeError("请求过于频繁，请稍后重试")

    response.raise_for_status()

    result = response.json()
    content = result["choices"][0]["message"]["content"]
    usage = result.get("usage", {})
    logger.info("DeepSeek 对话响应成功（输入 %d tokens, 输出 %d tokens）",
                usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))

    return content.strip()


# =================================================================
#  Excel 导入/同步错误诊断
# =================================================================

async def diagnose_excel_errors(
    errors: list,
    model_fields: dict,
    source: str = "import",
    model: str = MODEL_NAME,
    max_tokens: int = 4000,
    temperature: float = 0.1,
) -> str:
    """
    调用 DeepSeek 诊断 Excel 批量导入/同步时产生的错误

    Args:
        errors: 错误列表，每项为 {"case_number": "xxx", "reason": "xxx"} 或 str
        model_fields: 数据库模型字段定义字典
        source: "import" 或 "sync"
        model: 模型名称
        max_tokens: 最大输出 token 数
        temperature: 生成温度（诊断需低温度，保证确定性）

    Returns:
        Markdown 格式的诊断报告
    """
    if not DEEPSEEK_API_KEY:
        raise ValueError("DeepSeek API Key 未配置")

    # 构建用户消息
    parts = []

    # 1. 错误列表
    parts.append("## 错误列表")
    parts.append(f"共 {len(errors)} 个错误：\n")
    for i, err in enumerate(errors, 1):
        if isinstance(err, dict):
            parts.append(f"{i}. 业务号: {err.get('case_number', '未知')} - 原因: {err.get('reason', '未知')}")
        else:
            parts.append(f"{i}. {err}")

    # 2. 数据库模型字段定义 — 优先使用完整的模型源码（最准确）
    source_code = model_fields.get('_source_code')
    if source_code:
        parts.append("\n## 数据库模型源代码（models/case.py）")
        parts.append("该文件定义了 Case、BankCase、CaseParty 三个模型的所有字段约束：")
        parts.append(f"```python\n{source_code}\n```")
    else:
        parts.append("\n## 数据库模型字段定义（源码未获取到，使用降级表格）")
        for model_name, fields in model_fields.items():
            if model_name.startswith('_'):
                continue
            parts.append(f"\n### {model_name}")
            parts.append("| 字段名 | 类型 | 说明 | 必填 |")
            parts.append("|--------|------|------|------|")
            for field_name, field_info in fields.items():
                comment = field_info.get('comment', '')[:60]
                col_type = field_info.get('type', '')
                nullable = "否" if not field_info.get('nullable', True) else "是"

                # 枚举类型：在类型列中显式标注所有允许的取值
                enums = field_info.get('enums')
                if enums:
                    enum_items = []
                    for v in enums:
                        if v == '':
                            enum_items.append("空字符串")
                        else:
                            enum_items.append(f"`{v}`")
                    parts.append(f"| `{field_name}` | **ENUM** ({', '.join(enum_items)}) | {comment} | {nullable} |")
                else:
                    parts.append(f"| `{field_name}` | {col_type} | {comment} | {nullable} |")

    parts.append(f"\n## 操作来源")
    parts.append(f"{'批量导入' if source == 'import' else '批量同步'}")

    user_message = "\n".join(parts)

    # 构建 API 请求
    url = f"{DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": EXCEL_ERROR_DIAGNOSE_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    logger.info("调用 DeepSeek 诊断 Excel 错误（错误数: %d）", len(errors))

    try:
        async with _LLM_SEMAPHORE:
            response = await _retry_with_backoff(_post_llm_request, url, headers, payload)
    except httpx.TimeoutException:
        logger.error("DeepSeek 诊断请求超时")
        raise RuntimeError(f"DeepSeek API 请求超时（{REQUEST_TIMEOUT}秒）")
    except httpx.ConnectError:
        logger.error("无法连接到 DeepSeek API")
        raise ConnectionError("无法连接到 DeepSeek API")
    except httpx.HTTPStatusError as e:
        logger.error("DeepSeek 诊断 HTTP 错误: %d", e.response.status_code)
        raise RuntimeError(f"DeepSeek API 返回 HTTP {e.response.status_code}")

    response.raise_for_status()
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    usage = result.get("usage", {})
    logger.info("诊断完成（输入 %d tokens, 输出 %d tokens）",
                usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))

    return content.strip()
