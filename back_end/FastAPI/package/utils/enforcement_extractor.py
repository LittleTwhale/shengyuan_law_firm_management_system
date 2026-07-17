"""
强制执行申请书要素提取器
使用 DeepSeek v4-flash 模型从 OCR 文本中提取强制执行申请书的关键字段，
填充到要素式强制执行申请书模板中。

复用 llm_client 的全局信号量和重试机制，使用独立的模型常量和超时配置。
"""
import asyncio
import json
import logging
import re
from typing import Optional

import httpx

from ..core.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
from .llm_client import _LLM_SEMAPHORE, _retry_with_backoff

logger = logging.getLogger("shengyuan_app.enforcement_extractor")

# =================================================================
#  强制执行申请书提取专用配置
# =================================================================

# 使用 v4-flash 模型（结构化提取不需要深度推理，flash 更快更便宜）
ENFORCEMENT_MODEL = "deepseek-v4-flash"

# 请求超时（秒）
ENFORCEMENT_TIMEOUT = 120

# 最大输出 token（JSON 结构约 80 个字段，8000 token 足够）
ENFORCEMENT_MAX_TOKENS = 8000


# =================================================================
#  System Prompt — 强制执行申请书字段定义
# =================================================================

ENFORCEMENT_SYSTEM_PROMPT = """你是一位专业的法律文书信息提取专家。你的任务是从强制执行申请书的 OCR 识别文本中，精确提取关键信息，输出为结构化的 JSON 对象，用于填充要素式强制执行申请书模板。

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
- 通常申请执行人是银行等金融机构（company），被执行人可能是公司或个人

## JSON 顶级结构

```json
{
  "applicant": {
    "type": "company 或 individual",
    "company": { 法人/非法人组织字段 },
    "individual": { 自然人字段 }
  },
  "has_agent": true 或 false,
  "agent": { 代理人字段 或 null },
  "executor": {
    "type": "company 或 individual",
    "company": { ... },
    "individual": { ... }
  },
  "execution_basis": { 执行依据信息 },
  "execution_matters": { 申请执行事项 },
  "preservation": { 保全信息 },
  "property_clues": "财产线索文本 或 null",
  "signature": { 落款 }
}
```

## 各字段详细定义

### applicant / executor 的 company 子对象
| 字段 | 类型 | 说明 |
|------|------|------|
| name | string/null | 名称 |
| address | string/null | 住所地（主要办事机构所在地） |
| registered_address | string/null | 注册地/登记地 |
| legal_representative | string/null | 法定代表人/负责人 |
| representative_position | string/null | 法定代表人职务 |
| representative_phone | string/null | 法定代表人联系电话 |
| uscc | string/null | 统一社会信用代码 |
| bank_account | string/null | 银行账号 |
| bank_name | string/null | 开户名 |
| bank_branch | string/null | 开户行 |
| entity_type | [string]/null | 类型数组，可选值：["有限责任公司","股份有限公司","其他企业法人","事业单位","社会团体","基金会","社会服务机构","机关法人","农村集体经济组织法人","城镇农村的合作经济组织法人","基层群众性自治组织法人","个人独资企业","合伙企业","不具有法人资格的专业服务机构","民营","其他"] |
| state_owned_detail | [string]/null | 所有制性质，可选值：["国有控股","参股"] |

### applicant / executor 的 individual 子对象
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
| id_type | string/null | 证件类型 |
| id_number | string/null | 证件号码 |
| bank_account | string/null | 银行账号（仅 applicant） |
| bank_name | string/null | 开户名（仅 applicant） |
| bank_branch | string/null | 开户行（仅 applicant） |

### agent（委托诉讼代理人）
| 字段 | 类型 | 说明 |
|------|------|------|
| name | string/null | 代理人姓名 |
| unit | string/null | 所在单位 |
| position | string/null | 职务 |
| phone | string/null | 联系电话 |
| authority | string/null | 代理权限："一般授权" 或 "特别授权" |

### execution_basis（执行依据信息）
| 路径 | 类型 | 说明 |
|------|------|------|
| execution_basis.document_type | [string]/null | 文书类型数组，可选值：["民事判决书","民事裁定书","民事调解书","制裁决定","支付令","刑事附带民事判决书","刑事附带民事调解书","刑事附带民事裁定书","行政判决书","行政裁定书","行政调解书","行政处罚决定","行政处理决定","仲裁裁决书","仲裁调解书","财产保全裁定","证据保全裁定","赋予强制执行效力的债权文书","其他"] |
| execution_basis.organization | string/null | 执行依据作出机构 |
| execution_basis.cause_of_action | string/null | 案由 |
| execution_basis.case_number | string/null | 文书号 |
| execution_basis.effective_year | string/null | 生效日期-年 |
| execution_basis.effective_month | string/null | 生效日期-月 |
| execution_basis.effective_day | string/null | 生效日期-日 |
| execution_basis.text_main | string/null | 执行依据判项主文（生效法律文书确定的给付内容） |

### execution_matters（申请执行事项）
| 路径 | 类型 | 说明 |
|------|------|------|
| execution_matters.summary | string/null | 申请执行事项概要 |
| execution_matters.types | [string]/null | 执行请求类型，可选值：["金钱给付","行为执行","交付特定物","其他"] |
| execution_matters.money_details | [string]/null | 金钱给付明细类型，可选值：["本金","一般债务利息","迟延履行利息","其他费用"] |
| execution_matters.amount_principal | string/null | 本金金额 |
| execution_matters.amount_interest | string/null | 一般债务利息金额 |
| execution_matters.amount_delayed_interest | string/null | 迟延履行利息金额 |
| execution_matters.amount_other_fees | string/null | 其他费用金额 |

### preservation（保全信息）
| 路径 | 类型 | 说明 |
|------|------|------|
| preservation.has_preservation | string/null | "有" 或 "无" |
| preservation.case_number | string/null | 保全案号 |
| preservation.expiry_year | string/null | 保全措施最早到期-年 |
| preservation.expiry_month | string/null | 保全措施最早到期-月 |
| preservation.expiry_day | string/null | 保全措施最早到期-日 |

### 其他
| 路径 | 类型 | 说明 |
|------|------|------|
| property_clues | string/null | 其他财产线索（被执行人的银行账户、房产、车辆等） |
| signature.name | string/null | 申请执行人（签字、盖章） |
| signature.year | string/null | 落款日期-年 |
| signature.month | string/null | 落款日期-月 |
| signature.day | string/null | 落款日期-日 |

## 特殊联动规则

1. has_agent 为 false → agent 下所有字段为 null
2. 如果原文完全没有提到某个子部分，对应字段全部设为 null
3. 注意区分"申请执行人"（applicant）和"被执行人"（executor），不要混淆
4. 执行依据信息通常来自生效判决书/调解书等文书，注意提取文书号、作出机构、生效日期等
"""

# 模板中所有 data-field 路径（硬编码，避免每次请求读磁盘）
ENFORCEMENT_FIELD_PATHS = [
    "agent.authority", "agent.name", "agent.phone", "agent.position", "agent.unit",
    "applicant.company.address", "applicant.company.bank_account", "applicant.company.bank_branch",
    "applicant.company.bank_name", "applicant.company.entity_type", "applicant.company.legal_representative",
    "applicant.company.name", "applicant.company.registered_address", "applicant.company.representative_phone",
    "applicant.company.representative_position", "applicant.company.state_owned_detail", "applicant.company.uscc",
    "applicant.individual.address", "applicant.individual.bank_account", "applicant.individual.bank_branch",
    "applicant.individual.bank_name", "applicant.individual.birth_day", "applicant.individual.birth_month",
    "applicant.individual.birth_year", "applicant.individual.ethnicity", "applicant.individual.gender",
    "applicant.individual.id_number", "applicant.individual.id_type", "applicant.individual.name",
    "applicant.individual.phone", "applicant.individual.position", "applicant.individual.residence",
    "applicant.individual.work_unit",
    "execution_basis.case_number", "execution_basis.cause_of_action", "execution_basis.document_type",
    "execution_basis.effective_day", "execution_basis.effective_month", "execution_basis.effective_year",
    "execution_basis.organization", "execution_basis.text_main",
    "execution_matters.amount_delayed_interest", "execution_matters.amount_interest",
    "execution_matters.amount_other_fees", "execution_matters.amount_principal",
    "execution_matters.money_details", "execution_matters.summary", "execution_matters.types",
    "executor.company.address", "executor.company.entity_type", "executor.company.legal_representative",
    "executor.company.name", "executor.company.registered_address", "executor.company.representative_phone",
    "executor.company.representative_position", "executor.company.state_owned_detail", "executor.company.uscc",
    "executor.individual.address", "executor.individual.birth_day", "executor.individual.birth_month",
    "executor.individual.birth_year", "executor.individual.ethnicity", "executor.individual.gender",
    "executor.individual.id_number", "executor.individual.id_type", "executor.individual.name",
    "executor.individual.phone", "executor.individual.position", "executor.individual.residence",
    "executor.individual.work_unit",
    "has_agent",
    "preservation.case_number", "preservation.expiry_day", "preservation.expiry_month",
    "preservation.expiry_year", "preservation.has_preservation",
    "property_clues",
    "signature.day", "signature.month", "signature.name", "signature.year",
]


def _build_extraction_prompt(ocr_text: str) -> tuple:
    """
    构建强制执行申请书提取 prompt

    Args:
        ocr_text: OCR 识别后的文本内容

    Returns:
        (system_prompt, user_prompt) 元组
    """
    system_prompt = ENFORCEMENT_SYSTEM_PROMPT

    # 拼接完整的 data-field 路径列表帮助模型理解输出结构
    field_list = "\n".join(f"- `{f}`" for f in sorted(ENFORCEMENT_FIELD_PATHS))
    system_prompt += (
        f"\n\n## 模板中的完整 data-field 路径列表（共 {len(ENFORCEMENT_FIELD_PATHS)} 个字段）\n"
        f"请确保输出的 JSON 路径与以下路径一致：\n\n{field_list}"
    )

    user_prompt = f"""请从以下强制执行申请书相关材料的 OCR 识别文本中提取关键信息，输出为 JSON 格式。

注意事项：
1. 仔细阅读 OCR 文本，识别申请执行人（applicant）、被执行人（executor）信息
2. 区分法人和自然人类型（银行等金融机构为 company，个人姓名为 individual）
3. 提取执行依据信息（文书类型、案号、作出机构、生效日期、判项主文）
4. 提取申请执行事项（金钱给付金额、行为执行等）
5. 提取保全信息和财产线索
6. **未识别到的字段必须设为 null**
7. **直接输出 JSON 对象，不要用 markdown 代码块包裹**

=== OCR 识别文本开始 ===
{ocr_text}
=== OCR 识别文本结束 ===

请输出 JSON："""

    return system_prompt, user_prompt


async def extract_enforcement_fields(ocr_text: str) -> dict:
    """
    调用 DeepSeek v4-flash 从 OCR 文本中提取强制执行申请书字段

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
        "model": ENFORCEMENT_MODEL,
        "messages": messages,
        "temperature": 0.2,  # 低温度确保提取结果确定性强
        "max_tokens": ENFORCEMENT_MAX_TOKENS,
        "stream": False,
        "response_format": {"type": "json_object"},  # 强制 JSON 输出
    }

    logger.info(
        "调用 DeepSeek v4-flash 提取强制执行申请书字段（OCR 文本长度: %d 字符）",
        len(ocr_text),
    )

    async def _do_request():
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(ENFORCEMENT_TIMEOUT, connect=30.0)
        ) as client:
            return await client.post(url, headers=headers, json=payload)

    try:
        async with _LLM_SEMAPHORE:
            response = await _retry_with_backoff(
                _do_request, max_retries=3, base_delay=1.0
            )
    except httpx.TimeoutException:
        logger.error("DeepSeek v4-flash 强制执行提取请求超时（%d秒）", ENFORCEMENT_TIMEOUT)
        raise RuntimeError(
            f"DeepSeek API 请求超时（{ENFORCEMENT_TIMEOUT}秒），请稍后重试"
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
        "DeepSeek v4-flash 强制执行提取完成（输入 %d tokens, 输出 %d tokens）",
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
        "强制执行申请书字段提取成功，顶层字段: %s",
        list(fields.keys()),
    )
    return fields
