"""
起诉状要素提取器
使用 DeepSeek v4-pro 模型从 OCR 文本中提取民事起诉状的关键字段，
填充到要素式起诉状模板中。

复用 llm_client 的全局信号量和重试机制，使用独立的模型常量和超时配置。
"""
import asyncio
import json
import logging
import os
import re
from typing import Optional

import httpx

from ..core.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
from .llm_client import _LLM_SEMAPHORE, _retry_with_backoff

logger = logging.getLogger("shengyuan_app.complaint_extractor")

# =================================================================
#  起诉状提取专用配置
# =================================================================

# 使用 v4-flash 模型（结构化提取不需要深度推理，flash 更快更便宜）
COMPLAINT_MODEL = "deepseek-v4-flash"

# 请求超时（秒）
COMPLAINT_TIMEOUT = 120

# 最大输出 token（JSON 结构约 100 个字段，8000 token 足够）
COMPLAINT_MAX_TOKENS = 8000

# HTML 模板路径（相对于本文件向上三级到 FastAPI 根目录）
_TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "static", "template", "formal_complaint_form.html",
)

# 模板内容缓存（启动时加载一次，避免每次请求都读磁盘）
_template_cache: Optional[str] = None


def _load_template_html() -> str:
    """加载要素式起诉状 HTML 模板（带缓存，启动时加载一次）"""
    global _template_cache
    if _template_cache is not None:
        return _template_cache
    try:
        with open(_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            _template_cache = f.read()
        logger.info("已加载起诉状模板，共 %d 字符", len(_template_cache))
        return _template_cache
    except Exception as e:
        logger.error("加载起诉状模板失败: %s", e)
        return ""


# =================================================================
#  System Prompt — 详细描述 JSON 输出格式和提取规则
# =================================================================

EXTRACTION_SYSTEM_PROMPT_BASE = """你是一位专业的法律文书信息提取专家。你的任务是从民事起诉状的 OCR 识别文本中，精确提取关键信息，输出为结构化的 JSON 对象，用于填充要素式起诉状模板。

## 核心输出原则

1. **输出必须是合法 JSON 对象**，不要包含 markdown 代码块标记
2. **未识别到的字段必须设为 null**，绝不可编造、猜测或假设
3. **金额字段**只提取纯数字（去掉"元"、"人民币"等单位和千分位逗号）
4. **日期字段**分别提取年、月、日为独立字段
5. **数组字段**的值必须从给定选项中选择，不要创造新选项

## 当事人类型判断（关键规则）

原文中提到的当事人需判断 `type`:
- 出现"公司"、"银行"、"有限责任公司"、"股份有限公司"、"分行"、"支行"等 → `"type": "company"`，填写 `company` 子对象，`individual` 子对象全部为 null
- 出现个人姓名（如"张三"、"李某某"）→ `"type": "individual"`，填写 `individual` 子对象，`company` 子对象全部为 null
- 通常原告是银行等金融机构（company），被告可能是公司或个人

## JSON 顶级结构

```json
{
  "plaintiff": {
    "type": "company 或 individual",
    "company": { 法人/非法人组织字段 },
    "individual": { 自然人字段 }
  },
  "has_agent": true 或 false,
  "agent": { 代理人字段 或 null },
  "delivery": { 送达地址字段 或 null },
  "electronic_service": { 电子送达字段 或 null },
  "defendant": {
    "type": "company 或 individual",
    "company": { ... },
    "individual": { ... }
  },
  "has_third_party": true 或 false,
  "third_party": {
    "type": "company 或 individual 或 null",
    "company": { ... 或 null },
    "individual": { ... 或 null }
  },
  "claims": { 诉讼请求和依据 },
  "jurisdiction": { 管辖约定 },
  "preservation": { 诉讼保全 },
  "facts": { 事实和理由 },
  "signature": { 落款 }
}
```

## 各字段详细定义

### plaintiff / defendant / third_party 的 company 子对象
| 字段 | 类型 | 说明 |
|------|------|------|
| name | string/null | 名称 |
| address | string/null | 住所地（主要办事机构所在地） |
| registered_address | string/null | 注册地/登记地 |
| legal_representative | string/null | 法定代表人/主要负责人 |
| representative_position | string/null | 法定代表人职务 |
| representative_phone | string/null | 法定代表人联系电话 |
| uscc | string/null | 统一社会信用代码 |
| entity_type | [string]/null | 类型数组，可选值：["有限责任公司","股份有限公司","上市公司","其他企业法人","事业单位","社会团体","基金会","社会服务机构","机关法人","农村集体经济组织法人","城镇农村的合作经济组织法人","基层群众性自治组织法人","个人独资企业","合伙企业","不具有法人资格的专业服务机构","国有","民营"] |
| state_owned_detail | [string]/null | 仅当 entity_type 包含"国有"时才填写，可选值：["控股","参股"] |

### plaintiff / defendant / third_party 的 individual 子对象
| 字段 | 类型 | 说明 |
|------|------|------|
| name | string/null | 姓名 |
| gender | string/null | 性别："男" 或 "女" |
| birth_year | string/null | 出生年份 |
| birth_month | string/null | 出生月份 |
| birth_day | string/null | 出生日期 |
| ethnicity | string/null | 民族 |
| work_unit | string/null | 工作单位 |
| position | string/null | 职务 |
| phone | string/null | 联系电话 |
| address | string/null | 住所地（户籍所在地） |
| residence | string/null | 经常居住地 |

### agent（委托诉讼代理人）
| 字段 | 类型 | 说明 |
|------|------|------|
| name | string/null | 代理人姓名 |
| unit | string/null | 所在单位 |
| position | string/null | 职务 |
| phone | string/null | 联系电话 |
| authority | string/null | 代理权限："一般授权" 或 "特别授权" |

### delivery（送达地址）
| 字段 | 类型 |
|------|------|
| address | string/null |
| recipient | string/null |
| phone | string/null |

### electronic_service（电子送达）
| 字段 | 类型 | 说明 |
|------|------|------|
| accepted | string/null | "是" 或 "否" |
| methods | [string]/null | 可选值：["短信","微信","传真","邮箱","其他"] |

### claims（诉讼请求和依据）
| 路径 | 类型 | 说明 |
|------|------|------|
| claims.principal.year/month/day | string/null | 本金计算截止日期 |
| claims.principal.amount | string/null | 尚欠本金金额 |
| claims.interest.year/month/day | string/null | 利息计算截止日期 |
| claims.interest.interest_amount | string/null | 欠利息金额 |
| claims.interest.compound_interest | string/null | 复利金额 |
| claims.interest.penalty | string/null | 罚息/违约金金额 |
| claims.interest.calculation_method | string/null | 计算方式说明 |
| claims.interest.request_until_paid | string/null | "是" 或 "否" |
| claims.early_repayment.requested | string/null | "是" 或 "否" |
| claims.early_repayment.types | [string]/null | 可选值：["提前还款(加速到期)","解除合同"] |
| claims.guarantee_rights.claimed | string/null | "是" 或 "否" |
| claims.guarantee_rights.content | string/null | 担保权利内容 |
| claims.realization_expenses.claimed | string/null | "是" 或 "否" |
| claims.realization_expenses.details | string/null | 费用明细 |
| claims.other_claims | string/null | 其他请求 |
| claims.total_amount | string/null | 标的总额 |
| claims.basis.contract | string/null | 合同约定依据 |
| claims.basis.law | string/null | 法律规定依据 |

### jurisdiction（管辖约定）
| 路径 | 类型 | 说明 |
|------|------|------|
| jurisdiction.has_clause | string/null | "有" 或 "无" |
| jurisdiction.clause_content | string/null | 合同条款及内容 |

### preservation（诉讼保全）
| 路径 | 类型 | 说明 |
|------|------|------|
| preservation.pre_litigation.done | string/null | "是" 或 "否" |
| preservation.pre_litigation.court | string/null | 保全法院 |
| preservation.pre_litigation.time | string/null | 保全时间 |
| preservation.litigation.requested | string/null | "是" 或 "否" |

### facts（事实和理由）
| 路径 | 类型 | 说明 |
|------|------|------|
| facts.contract_signing | string/null | 合同签订情况（名称、编号、时间、地点等） |
| facts.lender | string/null | 贷款人 |
| facts.borrower | string/null | 借款人 |
| facts.loan_amount_agreed | string/null | 约定借款金额 |
| facts.loan_amount_actual | string/null | 实际发放金额 |
| facts.loan_term.is_due | string/null | "是" 或 "否" |
| facts.loan_term.start_year/month/day | string/null | 借款期限起 |
| facts.loan_term.end_year/month/day | string/null | 借款期限止 |
| facts.interest_rate.has_rate | string/null | 有利率时为 "true" |
| facts.interest_rate.rate | string/null | 利率百分比 |
| facts.interest_rate.rate_clause | string/null | 利率合同条款号 |
| facts.interest_rate.has_overdue_rate | string/null | 有逾期上浮时为 "true" |
| facts.interest_rate.overdue_rate | string/null | 逾期上浮利率 |
| facts.interest_rate.overdue_clause | string/null | 逾期上浮条款号 |
| facts.interest_rate.has_compound_interest | string/null | 有复利时为 "true" |
| facts.interest_rate.compound_interest_clause | string/null | 复利条款号 |
| facts.interest_rate.has_penalty | string/null | 有罚息时为 "true" |
| facts.interest_rate.penalty_rate | string/null | 罚息利率 |
| facts.interest_rate.penalty_clause | string/null | 罚息条款号 |
| facts.loan_disbursement.year/month/day | string/null | 借款发放日期 |
| facts.loan_disbursement.amount | string/null | 发放金额 |
| facts.repayment_method | [string]/null | 可选值：["等额本息","等额本金","到期一次性还本付息","按月计息、到期一次性还本","按季计息、到期一次性还本","按年计息、到期一次性还本","其他"] |
| facts.repayment_status.principal_paid | string/null | 已还本金 |
| facts.repayment_status.interest_paid | string/null | 已还利息 |
| facts.repayment_status.interest_paid_to_year/month/day | string/null | 还息截止日期 |
| facts.is_overdue | string/null | "是" 或 "否" |
| facts.overdue_period | string/null | 逾期时间描述 |
| facts.has_property_guarantee | string/null | "是" 或 "否" |
| facts.property_guarantee_date | string/null | 物的担保签订时间 |
| facts.guarantor | string/null | 担保人 |
| facts.collateral | string/null | 担保物 |
| facts.is_max_amount_guarantee | string/null | "是" 或 "否" |
| facts.max_amount_determination_date | string/null | 担保债权确定时间 |
| facts.max_amount_limit | string/null | 担保额度 |
| facts.is_registered | string/null | "是" 或 "否" |
| facts.registration_types | [string]/null | 可选值：["正式登记","预告登记"] |
| facts.has_guarantee_contract | string/null | "是" 或 "否" |
| facts.guarantee_contract_date | string/null | 保证合同签订时间 |
| facts.guarantee_person | string/null | 保证人 |
| facts.guarantee_contract_content | string/null | 保证合同主要内容 |
| facts.guarantee_methods | [string]/null | 可选值：["一般保证","连带责任保证"] |
| facts.other_guarantee.exists | string/null | "是" 或 "否" |
| facts.other_guarantee.form | string/null | 其他担保形式 |
| facts.other_guarantee.date | string/null | 其他担保签订时间 |
| facts.other_notes | string/null | 其他需要说明的内容 |
| facts.evidence_list | string/null | 证据清单 |

### signature（落款）
| 路径 | 类型 |
|------|------|
| signature.name | string/null | 具状人 |
| signature.year | string/null |
| signature.month | string/null |
| signature.day | string/null |

## 特殊联动规则

1. entity_type 包含"国有" → state_owned_detail 必须填写，可选 ["控股"] 或 ["参股"] 或 ["控股","参股"]
2. has_agent 为 false → agent 下所有字段为 null
3. has_third_party 为 false → third_party 下所有字段为 null（type 也可为 null）
4. 如果原文完全没有提到某个子部分（如 electronic_service），对应字段全部设为 null
"""


def _build_extraction_prompt(ocr_text: str) -> tuple:
    """
    构建提取 prompt

    Args:
        ocr_text: OCR 识别后的文本内容

    Returns:
        (system_prompt, user_prompt) 元组
    """
    system_prompt = EXTRACTION_SYSTEM_PROMPT_BASE

    # 加载模板，提取所有 data-field 路径列表帮助模型理解字段
    template_html = _load_template_html()
    if template_html:
        fields = set(re.findall(r'data-field="([^"]+)"', template_html))
        sorted_fields = sorted(fields)
        field_list = "\n".join(f"- `{f}`" for f in sorted_fields)
        system_prompt += (
            f"\n\n## 模板中的完整 data-field 路径列表（共 {len(sorted_fields)} 个字段）\n"
            f"请确保输出的 JSON 路径与以下路径一致：\n\n{field_list}"
        )

    user_prompt = f"""请从以下民事起诉状的 OCR 识别文本中提取关键信息，输出为 JSON 格式。

注意事项：
1. 仔细阅读 OCR 文本，识别原告、被告、第三人信息
2. 区分法人和自然人类型（银行等金融机构为 company，个人姓名为 individual）
3. 提取诉讼请求中的金额、利息、担保等信息
4. 提取事实与理由部分的关键要素（合同、利率、还款情况等）
5. **未识别到的字段必须设为 null**
6. **直接输出 JSON 对象，不要用 markdown 代码块包裹**

=== OCR 识别文本开始 ===
{ocr_text}
=== OCR 识别文本结束 ===

请输出 JSON："""

    return system_prompt, user_prompt


async def extract_complaint_fields(ocr_text: str) -> dict:
    """
    调用 DeepSeek v4-pro 从 OCR 文本中提取起诉状字段

    Args:
        ocr_text: OCR 识别后的文本内容（至少 20 个有效字符）

    Returns:
        提取到的字段字典

    Raises:
        ValueError: API Key 未配置或 OCR 文本过短
        RuntimeError: API 调用失败或返回内容无法解析
        ConnectionError: 无法连接到 API
    """
    if not DEEPSEEK_API_KEY:
        raise ValueError("DeepSeek API Key 未配置，请在 .env 文件中设置 DEEPSEEK_API_KEY")

    if not ocr_text or len(ocr_text.strip()) < 20:
        raise ValueError("OCR 文本内容过短（少于 20 字符），无法提取有效信息")

    system_prompt, user_prompt = _build_extraction_prompt(ocr_text)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    url = f"{DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": COMPLAINT_MODEL,
        "messages": messages,
        "temperature": 0.2,  # 低温度确保提取结果确定性强
        "max_tokens": COMPLAINT_MAX_TOKENS,
        "stream": False,
        "response_format": {"type": "json_object"},  # 强制 JSON 输出
    }

    logger.info(
        "调用 DeepSeek v4 提取起诉状字段（OCR 文本长度: %d 字符）",
        len(ocr_text),
    )

    async def _do_request():
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(COMPLAINT_TIMEOUT, connect=30.0)
        ) as client:
            return await client.post(url, headers=headers, json=payload)

    try:
        async with _LLM_SEMAPHORE:
            response = await _retry_with_backoff(
                _do_request, max_retries=3, base_delay=1.0
            )
    except httpx.TimeoutException:
        logger.error("DeepSeek v4-pro 提取请求超时（%d秒）", COMPLAINT_TIMEOUT)
        raise RuntimeError(
            f"DeepSeek API 请求超时（{COMPLAINT_TIMEOUT}秒），请稍后重试"
        )
    except httpx.ConnectError:
        logger.error("无法连接到 DeepSeek API（%s）", DEEPSEEK_BASE_URL)
        raise ConnectionError(
            f"无法连接到 DeepSeek API（{DEEPSEEK_BASE_URL}），请检查网络连接"
        )
    except httpx.HTTPStatusError as e:
        logger.error(
            "DeepSeek API HTTP 错误: %d, 响应: %s",
            e.response.status_code,
            e.response.text[:300],
        )
        raise RuntimeError(
            f"DeepSeek API 返回 HTTP {e.response.status_code}，请查看日志获取详细信息"
        )

    if response.status_code != 200:
        err_body = response.text[:500]
        logger.error(
            "DeepSeek API 非 200 响应: %d, 内容: %s",
            response.status_code,
            err_body,
        )
        raise RuntimeError(f"DeepSeek API 请求失败: HTTP {response.status_code}")

    result = response.json()
    content = result["choices"][0]["message"]["content"]
    usage = result.get("usage", {})
    logger.info(
        "DeepSeek v4-pro 提取完成（输入 %d tokens, 输出 %d tokens）",
        usage.get("prompt_tokens", 0),
        usage.get("completion_tokens", 0),
    )

    # ── 容错：正则提取 JSON（防御 LLM 偶尔输出 markdown 代码块）──
    json_str = content.strip()

    # 1) 尝试去掉 markdown 代码块标记
    md_match = re.search(
        r"```(?:json)?\s*\n?(.*?)\n?```", json_str, re.DOTALL
    )
    if md_match:
        json_str = md_match.group(1).strip()
        logger.info("从 markdown 代码块中提取 JSON")

    # 2) 尝试找到最外层的 { ... }
    brace_match = re.search(r"\{.*\}", json_str, re.DOTALL)
    if brace_match:
        json_str = brace_match.group(0)

    # 3) 解析 JSON
    try:
        fields = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(
            "JSON 解析失败，原始内容前 500 字符: %s", content[:500]
        )
        raise RuntimeError(
            f"DeepSeek 返回的内容无法解析为 JSON: {e}"
        )

    if not isinstance(fields, dict):
        raise RuntimeError("DeepSeek 返回的 JSON 不是一个对象")

    logger.info(
        "起诉状字段提取成功，顶层字段: %s",
        list(fields.keys()),
    )
    return fields
