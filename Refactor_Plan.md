# 案件当事人字段重构指南

> **目标**: 将 `cases` 表中的 `client_name`, `client_id_number`, `client_phone`, `plaintiff`, `appellant_info`, `extra_appellant_info`, `defendant`, `third_party` 共 8 个字段全部废弃，统一迁移至 `case_parties` 表管理。
>
> **日期**: 2026-05-25
>
> **前置阅读**: 请先阅读本指南「第一章 全库搜索指引」定位所有引用，再按「第二章 重构方案」逐文件修改，最后执行「第三章 数据库清理」。

---

## 目录

- [一、全库搜索指引](#一全库搜索指引)
- [二、重构方案（按文件分类）](#二重构方案按文件分类)
  - [2.1 后端 — 数据模型层](#21-后端--数据模型层)
  - [2.2 后端 — Schema 层](#22-后端--schema-层)
  - [2.3 后端 — CRUD 层 (crud/case.py)](#23-后端--crud-层-crudcasepy)
  - [2.4 后端 — CRUD 层 (crud/case_review.py)](#24-后端--crud-层-crudcase_reviewpy)
  - [2.5 后端 — CRUD 层 (crud/electronic_volume_crud.py)](#25-后端--crud-层-crudelectronic_volume_crudpy)
  - [2.6 后端 — CRUD 层 (crud/finance_crud.py)](#26-后端--crud-层-crudfinance_crudpy)
  - [2.7 后端 — API 层 (api/case_manage.py)](#27-后端--api-层-apicase_managepy)
  - [2.8 后端 — API 层 (api/case_review.py)](#28-后端--api-层-apicase_reviewpy)
  - [2.9 后端 — API 层 (api/user_profile.py)](#29-后端--api-层-apiuser_profilepy)
  - [2.10 前端 — CaseForm.vue](#210-前端--caseformvue)
  - [2.11 前端 — GeneralCaseDetail.vue](#211-前端--generalcasedetailvue)
  - [2.12 前端 — CasesPage.vue](#212-前端--casespagevue)
  - [2.13 前端 — BankCasesPage.vue](#213-前端--bankcasespagevue)
  - [2.14 前端 — CaseReviewPage.vue](#214-前端--casereviewpagevue)
  - [2.15 前端 — FinancePage.vue](#215-前端--financepagevue)
  - [2.16 前端 — DashBoard.vue](#216-前端--dashboardvue)
  - [2.17 前端 — EventReminderPage.vue](#217-前端--eventreminderpagevue)
- [三、数据库清理 SQL](#三数据库清理-sql)

---

## 一、全库搜索指引

在开始重构前，请使用以下命令精准定位所有引用位置。

### 1.1 后端搜索（`back_end\FastAPI\package\`）

在项目根目录 `D:\syls` 下打开终端，执行：

```bash
# 依次搜索 8 个废弃字段（后端 Python 文件）
cd /d/syls/back_end/FastAPI/package

# 字段 1: client_name
grep -rn "client_name" --include="*.py" .

# 字段 2: client_id_number
grep -rn "client_id_number" --include="*.py" .

# 字段 3: client_phone
grep -rn "client_phone" --include="*.py" .

# 字段 4: plaintiff
grep -rn "plaintiff" --include="*.py" .

# 字段 5: appellant_info
grep -rn "appellant_info" --include="*.py" .

# 字段 6: extra_appellant_info
grep -rn "extra_appellant_info" --include="*.py" .

# 字段 7: defendant
grep -rn "defendant" --include="*.py" .

# 字段 8: third_party
grep -rn "third_party" --include="*.py" .
```

> **注意**: `grep -rn "defendant"` 会同时命中 `defendant_paid_lawyer_fee` 字段（该字段**不是废弃字段**，属于 `bank_case_details` 表），请手动过滤。

### 1.2 前端搜索（`frontend\sy_lawyers_office\src\views\`）

```bash
cd /d/syls/frontend/sy_lawyers_office/src/views

# 依次搜索 8 个废弃字段（前端 .vue / .js 文件）
grep -rn "client_name" --include="*.vue" --include="*.js" .
grep -rn "client_id_number" --include="*.vue" --include="*.js" .
grep -rn "client_phone" --include="*.vue" --include="*.js" .
grep -rn "plaintiff" --include="*.vue" --include="*.js" .
grep -rn "appellant_info" --include="*.vue" --include="*.js" .
grep -rn "extra_appellant_info" --include="*.vue" --include="*.js" .
grep -rn "defendant" --include="*.vue" --include="*.js" .
grep -rn "third_party" --include="*.vue" --include="*.js" .
```

### 1.3 VS Code 全局搜索（替代方案）

1. 按 `Ctrl+Shift+F` 打开全局搜索
2. 在 "files to include" 中输入: `back_end/FastAPI/package/**/*.py, frontend/sy_lawyers_office/src/views/**/*.vue`
3. 依次搜索上述 8 个字段名，逐一核对每个命中项

---

## 二、重构方案（按文件分类）

### 核心映射关系速查

| 废弃字段 | case_parties 替代查询逻辑 |
|---------|--------------------------|
| `client_name` | `case.parties` 中 `party_type` 含 `'委托'` 的记录，取 `name`，用 `、` 拼接 |
| `client_id_number` | 第一个 `'委托'` 类型当事人的 `id_number` |
| `client_phone` | 第一个 `'委托'` 类型当事人的 `phone` |
| `plaintiff` | `party_type` 为 `'原告'` / `'申请人'` / `'上诉人'` 的记录，取 `name` 拼接 |
| `appellant_info` | `party_type` 为 `'上诉人'` 的记录的额外信息（如 `address` 等） |
| `extra_appellant_info` | `party_type` 为 `'被上诉人'` 的记录的额外信息 |
| `defendant` | `party_type` 为 `'被告'` / `'被申请人'` / `'被上诉人'` 的记录，取 `name` 拼接 |
| `third_party` | `party_type` 为 `'第三人'` 的记录，取 `name` 拼接 |

---

### 2.1 后端 — 数据模型层

#### 文件: `back_end\FastAPI\package\models\case.py`

##### 2.1.1 删除 Column 定义（第 14–16 行 + 第 29–33 行）

**旧代码:**
```python
# 第 14-16 行
client_name = Column(String(100), nullable=False, comment="委托人")
client_id_number = Column(String(18), nullable=True, comment="委托人身份证号/单位税号")
client_phone = Column(String(20), nullable=True, comment="委托人电话")

# 第 29-33 行
plaintiff = Column(String(100), nullable=False, comment="原告/申请人")
appellant_info = Column(Text, nullable=True, comment="上诉人信息补充")
extra_appellant_info = Column(Text, nullable=True, comment="补上诉人或补告信息补充")
defendant = Column(String(100), nullable=True, comment="被告")
third_party = Column(String(255), nullable=True, comment="第三人")
```

**新代码:**
```python
# 全部删除上述 8 行。当事人信息已完全迁移至 case_parties 表，通过 Case.parties 关系访问。
```

---

### 2.2 后端 — Schema 层

#### 文件: `back_end\FastAPI\package\schemas\case.py`

该文件中有多个 Pydantic Schema 类包含废弃字段，需要逐一清理。

##### 2.2.1 `CaseOut` 及其相关 Output Schema

搜索 `client_name: Optional[str]`、`client_id_number`、`client_phone`、`plaintiff`、`appellant_info`、`extra_appellant_info`、`defendant`、`third_party` 等字段定义，全部删除。

涉及的 Schema 类:
- `CaseOut` (约第 437 行 / 473 行 / 506 行)
- `CaseListItem` (约第 279 行)
- `CaseUpdate` (约第 358 行)
- `CaseReviewOut` (约第 203 行)

**旧代码示例（CaseListItem）:**
```python
client_name: Optional[str] = Field(None, description="委托人 / Client name")
client_id_number: Optional[str] = Field(None, description="委托人身份证号/单位税号 / Client ID / Tax number")
client_phone: Optional[str] = Field(None, description="委托人电话 / Client phone")
# ...
plaintiff: Optional[str] = Field(None, description="原告 / Plaintiff")
appellant_info: Optional[str] = Field(None, description="上诉人信息 / Appellant info")
extra_appellant_info: Optional[str] = Field(None, description="被上诉人信息 / Extra appellant info")
defendant: Optional[str] = Field(None, description="被告 / Defendant")
third_party: Optional[str] = Field(None, description="第三人 / Third party")
```

**新代码:**
```python
# 全部删除以上 8 行。前端/API 通过 case.parties 列表获取当事人信息。
```

> **关键点**: `CaseOut` 中已经包含 `parties: List[CasePartyOut] = []` 字段，前端可以直接通过 `case.parties` 获取完整的当事人列表，无需再维护旧的字符串字段。

##### 2.2.2 文件: `back_end\FastAPI\package\schemas\electronic_volume_schema.py`

搜索并删除:
```python
# 删除此行（第 16 行）
client_name: Optional[str] = None
```

##### 2.2.3 文件: `back_end\FastAPI\package\schemas\finance_schema.py`

搜索并删除:
```python
# 删除此行（第 103 行）
client_name: Optional[str] = None
```

---

### 2.3 后端 — CRUD 层 (crud/case.py)

这是改动量最大的文件，涉及约 30+ 处引用。

#### 2.3.1 删除 `_sync_legacy_fields()` 辅助函数（约第 367–399 行）

**旧代码（完整函数）:**
```python
# 辅助函数：将当事人列表转换为逗号分隔字符串（用于兼容旧字段）
def _sync_legacy_fields(parties_data: list) -> dict:
    clients = []
    plaintiffs = []
    defendants = []
    for p in parties_data:
        p_type = p.party_type if hasattr(p, 'party_type') else p.get('party_type')
        p_name = p.name if hasattr(p, 'name') else p.get('name')

        if p_type in ['原告', '申请人', '上诉人']:
            plaintiffs.append(p_name)
        elif p_type in ['被告', '被申请人', '被上诉人']:
            defendants.append(p_name)
        elif p_type == '委托人':
            clients.append(p)

    result = {
        "plaintiff": "、".join(plaintiffs) if plaintiffs else None,
        "defendant": "、".join(defendants) if defendants else None,
        "client_name": "、".join([c.name if hasattr(c, 'name') else c.get('name') for c in clients]) if clients else None
    }

    if clients:
        first_client = clients[0]
        phone = first_client.phone if hasattr(first_client, 'phone') else first_client.get('phone')
        id_number = first_client.id_number if hasattr(first_client, 'id_number') else first_client.get('id_number')
        result["client_phone"] = phone
        result["client_id_number"] = id_number

    return result
```

**新代码:**
```python
# 整个函数删除。旧字段同步逻辑不再需要。
```

#### 2.3.2 `create_case()` 中删除 legacy 回写逻辑（约第 457–469 行）

**旧代码:**
```python
    # 如果前端传了当事人列表，自动生成旧字段字符串
    if case_in.parties:
        legacy_update = _sync_legacy_fields(case_in.parties)
        if legacy_update["plaintiff"]:
            case_data["plaintiff"] = legacy_update["plaintiff"]
        if legacy_update["defendant"]:
            case_data["defendant"] = legacy_update["defendant"]
        if legacy_update.get("client_name"):
            case_data["client_name"] = legacy_update["client_name"]
        if legacy_update.get("client_phone"):
            case_data["client_phone"] = legacy_update["client_phone"]
        if legacy_update.get("client_id_number"):
            case_data["client_id_number"] = legacy_update["client_id_number"]
```

**新代码:**
```python
    # 删除整个代码块。case_parties 表已独立存储，无需回写旧字段。
```

#### 2.3.3 `update_case()` 中删除 legacy 同步逻辑（约第 638–649 行）

**旧代码:**
```python
        # C. 同步更新旧字段
        legacy_update = _sync_legacy_fields(case_in.parties)
        if legacy_update["plaintiff"] is not None:
            case.plaintiff = legacy_update["plaintiff"]
        if legacy_update["defendant"] is not None:
            case.defendant = legacy_update["defendant"]
        if legacy_update.get("client_name"):
            case.client_name = legacy_update["client_name"]
        if legacy_update.get("client_phone"):
            case.client_phone = legacy_update["client_phone"]
        if legacy_update.get("client_id_number"):
            case.client_id_number = legacy_update["client_id_number"]
```

**新代码:**
```python
        # 删除整个代码块。当事人数据仅存储在 case_parties 表中。
```

#### 2.3.4 查询函数中的 `client_name` 搜索兼容逻辑

涉及位置:
- `list_cases_by_user_role()`: 约第 251–257 行
- `list_cases()`: 约第 334–340 行
- `export_cases_to_excel()`: 约第 1137–1144 行

**旧代码（典型模式）:**
```python
if client_name:
    query = query.filter(
        or_(
            Case.client_name.like(f"%{client_name}%"),
            Case.parties.any(
                and_(CaseParty.party_type.like('%委托%'), CaseParty.name.like(f"%{client_name}%"))
            )
        )
    )
```

**新代码:**
```python
if client_name:
    query = query.filter(
        Case.parties.any(
            and_(CaseParty.party_type.like('%委托%'), CaseParty.name.like(f"%{client_name}%"))
        )
    )
```

> **说明**: 移除 `Case.client_name.like(...)` 分支，仅保留通过 `Case.parties.any(...)` 查询 `case_parties` 表的逻辑。

#### 2.3.5 `_enrich_case_item()` 中的 party 数据聚合（约第 367–399 行区域）

当前位置已经在 `_sync_legacy_fields()` 中有 client/plaintiff/defendant 的聚合逻辑。删除整个函数后，此部分自然消失。

#### 2.3.6 Excel 导出中的 party 数据构建（约第 1227–1302 行）

此处的 `plaintiffs_name` / `defendants_name` 等变量是从 `case.parties` 中提取的，**本身就是新的正确逻辑**，不需要改动。仅需确认不再从 `Case` 旧字段中读取。

#### 2.3.7 日程安排事件中的 client_name（约第 969、988、1039、1057 行）

**旧代码（第 969 行）:**
```python
real_client_name = "、".join(clients) if clients else (case.client_name or "")
```

**新代码:**
```python
real_client_name = "、".join(clients) if clients else ""
```

**旧代码（第 1039 行）:**
```python
c_client = "、".join(clients) if clients else (sched.related_case.client_name or "")
```

**新代码:**
```python
c_client = "、".join(clients) if clients else ""
```

> **说明**: 删掉 `case.client_name` 兜底回退，因为旧字段将不存在。

---

### 2.4 后端 — CRUD 层 (crud/case_review.py)

#### 2.4.1 利益冲突检测中的 client_name 回退（约第 149–150 行）

**旧代码:**
```python
if not new_client_names and current_case.client_name:
    new_client_names.add(current_case.client_name.strip())
```

**新代码:**
```python
# 删除这两行。client_name 旧字段已废弃，new_client_names 完全从 case.parties 中提取。
```

#### 2.4.2 文书生成 context 构建中的旧字段回退（约第 537–546 行）

**旧代码:**
```python
if not clients and case.client_name:
    context["client_name"] = case.client_name
# ...
context["client_phone"] = case.client_phone
# ...
if not plaintiffs and case.plaintiff:
    context["plaintiff"] = case.plaintiff
# ...
if not defendants and case.defendant:
    context["defendant"] = case.defendant
```

**新代码:**
```python
# 删除所有上述回退逻辑。context 中的字段完全由 case.parties 中提取的数据填充。
```

#### 2.4.3 审核邮件中的 client_name（约第 89 行）

**旧代码:**
```python
<p><strong>委托人：</strong>{case.client_name or '--'}</p>
```

**新代码:**
```python
<p><strong>委托人：</strong>{join_str(clients) or '--'}</p>
```
> 需要在函数开头处先提取 `clients` 列表（与 `plaintiffs`、`defendants` 类似的处理方式）。

---

### 2.5 后端 — CRUD 层 (crud/electronic_volume_crud.py)

#### 第 69 行：搜索过滤中的 client_name

**旧代码:**
```python
Case.client_name.ilike(search),
```

**新代码:**
```python
# 替换为通过 case_parties 关系搜索
Case.parties.any(
    and_(CaseParty.party_type.like('%委托%'), CaseParty.name.ilike(search))
),
```

---

### 2.6 后端 — CRUD 层 (crud/finance_crud.py)

#### 2.6.1 第 61 行：财务搜索过滤

**旧代码:**
```python
Case.client_name.ilike(search)
```

**新代码:**
```python
# 替换为通过 case_parties 关系搜索
Case.parties.any(
    and_(CaseParty.party_type.like('%委托%'), CaseParty.name.ilike(search))
)
```

#### 2.6.2 第 455 行：查询字段列表

**旧代码:**
```python
c.case_number, c.client_name, c.case_category, main_lawyer_name,
```

**新代码:**
```python
# 在查询前先通过 joinedload 预加载 parties，然后在遍历时动态提取：
# clients = [p.name for p in c.parties if '委托' in (p.party_type or '')]
# client_name_str = "、".join(clients)
c.case_number, c.case_category, main_lawyer_name,
```

#### 2.6.3 第 485、513、541 行：c_info 中的 client_name

**旧代码:**
```python
c_info = [f.case.case_number, f.case.client_name]
```

**新代码:**
```python
# 在构建 c_info 前先提取委托人名称
clients = [p.name for p in f.case.parties if p.party_type and '委托' in p.party_type]
c_info = [f.case.case_number, "、".join(clients)]
```

---

### 2.7 后端 — API 层 (api/case_manage.py)

#### 2.7.1 `aggregate_client_names()` 辅助函数（第 36–42 行）

**旧代码:**
```python
def aggregate_client_names(case_obj: Case) -> str:
    """从 CaseParty 中提取委托人名称并拼接"""
    if not case_obj.parties:
        return case_obj.client_name or ""
    clients = [p.name for p in case_obj.parties if p.party_type and '委托' in p.party_type and p.name]
    return "、".join(clients) if clients else (case_obj.client_name or "")
```

**新代码:**
```python
def aggregate_client_names(case_obj: Case) -> str:
    """从 CaseParty 中提取委托人名称并拼接"""
    if not case_obj.parties:
        return ""
    clients = [p.name for p in case_obj.parties if p.party_type and '委托' in p.party_type and p.name]
    return "、".join(clients)
```

#### 2.7.2 冲突检测中的 `case_data.client_name` / `case_data.defendant` 回退（约第 291–292、354–356 行）

**旧代码（第 291–292 行）:**
```python
if not new_client_names and case_data.client_name:
    new_client_names.add(case_data.client_name.strip())
```

**新代码:**
```python
# 删除这两行。new_client_names 完全从 parties 参数中提取。
```

**旧代码（第 354–356 行）:**
```python
if not new_case_opponents and case_data.defendant and client_side == "A":
    new_case_opponents = set(d.strip() for d in split_with_separators(case_data.defendant, separators) if d.strip())
```

**新代码:**
```python
# 删除这个回退逻辑。对立方信息完全从 parties 参数中提取。
```

---

### 2.8 后端 — API 层 (api/case_review.py)

#### 2.8.1 审核逻辑中的旧字段回退（约第 66–67 行）

**旧代码:**
```python
if not new_client_names and current_case["client_name"]:
    new_client_names.add(current_case["client_name"].strip())
```

**新代码:**
```python
# 删除这两行。
```

#### 2.8.2 审核列表中的 client_name 聚合（约第 183–190 行）

**旧代码:**
```python
# 拦截转换：用 CaseParty 中的委托人覆盖旧的 client_name
# ...
simple.client_name = "、".join(clients)
```

**新代码:**
```python
# simple.client_name 赋值保持不变（Schema 中的 client_name 字段将在第 2.2 节统一删除）
# 如果 Schema 已删除 client_name，此处改为通过 parties 列表传递：
# simple.parties = [...]  # 前端直接使用 parties 展示
```

> **过渡期建议**: 如果前端尚未完全适配，可暂时保留 `simple.client_name` 的赋值逻辑（取值来源已经是 CaseParty），等前端改造完成后再删除 Schema 中的 `client_name` 字段。

#### 2.8.3 审核列表查询字段（约第 218 行）

**旧代码:**
```python
Case.client_name,
```

**新代码:**
```python
# 删除这一行。加入 joinedload(Case.parties) 以确保 parties 被预加载。
```

#### 2.8.4 审核结果字典中的旧字段（约第 234 行）

**旧代码:**
```python
"client_name": r.client_name or "",
```

**新代码:**
```python
# 改为动态提取:
"client_name": "、".join([p.name for p in r.parties if '委托' in (p.party_type or '')]),
```

---

### 2.9 后端 — API 层 (api/user_profile.py)

#### 第 127–133 行：用户档案中的 client_name 回退

**旧代码:**
```python
# 为了平滑过渡兼容历史旧数据，如果没查到独立当事人，可以暂时 fallback 到 c.client_name
real_client_name = "、".join(clients) if clients else (c.client_name or "")
# ...
"client_name": real_client_name
```

**新代码:**
```python
real_client_name = "、".join(clients) if clients else ""
# ...
"client_name": real_client_name
```

---

### 2.10 前端 — CaseForm.vue

#### 2.10.1 data() 中的旧字段定义（约第 269–272 行）

**旧代码:**
```javascript
// 旧字段保留（用于兼容，提交时填充）
client_name: null,
client_id_number: null,
client_phone: null,
```

**新代码:**
```javascript
// 删除以上 4 行。
```

#### 2.10.2 编辑回显时的旧字段兼容逻辑（约第 471–501 行）

data() 中已经定义了 `party_clients`、`party_plaintiffs`、`party_defendants`、`party_third_parties` 等数组。当后端返回的 `data.parties` 存在时会优先使用新的 party 数据。

**旧代码（第 471–501 行，`else` 分支）:**
```javascript
} else {
  if (data.client_name) {
    const clients = data.client_name.split(/[,，、]/).filter((s) => s)
    clients.forEach((c, idx) => {
      formData.party_clients.push({
        party_type: '委托人',
        name: c,
        phone: idx === 0 ? data.client_phone : '',
        id_number: idx === 0 ? data.client_id_number : '',
        address: '',
      })
    })
  }
  if (data.plaintiff) {
    const plaintiffs = data.plaintiff.split(/[,，、]/).filter((s) => s)
    plaintiffs.forEach((p) => {
      formData.party_plaintiffs.push({ party_type: '原告', name: p })
    })
  }
  if (data.defendant) {
    const defendants = data.defendant.split(/[,，、]/).filter((s) => s)
    defendants.forEach((d) => {
      formData.party_defendants.push({ party_type: '被告', name: d })
    })
  }
  if (data.third_party) {
    const thirdParties = data.third_party.split(/[,，、]/).filter((s) => s)
    thirdParties.forEach((t) => {
      formData.party_third_parties.push({ party_type: '第三人', name: t })
    })
  }
}
```

**新代码:**
```javascript
// 删除整个 else 分支。数据迁移工作已在后端完成，
// 历史数据已全部迁移至 case_parties 表，data.parties 始终存在。
}
```

> **注意**: 删除 else 分支后，外层的 `if (data.parties && data.parties.length > 0)` 结构中的反括号需对应调整。

#### 2.10.3 submitData 中的旧字段填充（约第 697–705 行）

**旧代码:**
```javascript
// 兼容旧字段 logic
if (submitData.party_clients && submitData.party_clients.length > 0) {
  const firstClient = submitData.party_clients[0]
  submitData.client_name = firstClient.name || ''
  submitData.client_phone = firstClient.phone || ''
  submitData.client_id_number = firstClient.id_number || ''
} else {
  submitData.client_name = ''
}
```

**新代码:**
```javascript
// 删除整个代码块。后端不再需要这些旧字段。
```

---

### 2.11 前端 — GeneralCaseDetail.vue

#### 2.11.1 `appellant_info` 和 `extra_appellant_info` 展示（第 119–124 行）

**旧代码:**
```html
<el-descriptions-item label="上诉人">{{
  caseData.appellant_info || '-'
}}</el-descriptions-item>
<el-descriptions-item label="被上诉人">{{
  caseData.extra_appellant_info || '-'
}}</el-descriptions-item>
```

**新代码:**
```html
<!-- 改为从 parties 计算属性获取 -->
<el-descriptions-item label="上诉人">{{
  partyAppellants.length > 0 ? partyAppellants.map(p => p.name).join('、') : '-'
}}</el-descriptions-item>
<el-descriptions-item label="被上诉人">{{
  partyAppellees.length > 0 ? partyAppellees.map(p => p.name).join('、') : '-'
}}</el-descriptions-item>
```

同时在 computed 中新增:
```javascript
const partyAppellants = computed(() =>
  (caseData.value.parties || []).filter(p => p.party_type === '上诉人')
)
const partyAppellees = computed(() =>
  (caseData.value.parties || []).filter(p => p.party_type === '被上诉人')
)
```

#### 2.11.2 `third_party` 回退展示（第 59 行）

**旧代码:**
```html
:empty-text="caseData.third_party || '-'"
```

**新代码:**
```html
<!-- 移除 empty-text 中的旧字段回退 -->
:empty-text="'-'"
```
> `partyThirdParties` computed 属性本身已经能从 `caseData.parties` 中提取第三人列表，无需旧字段回退。

---

### 2.12 前端 — CasesPage.vue

#### 第 125 行：表格列中的 client_name

**旧代码:**
```html
<el-table-column prop="client_name" label="委托人" min-width="220" align="center" />
```

**新代码:**
```html
<el-table-column label="委托人" min-width="220" align="center">
  <template #default="{ row }">
    {{ getClientNames(row.parties) || '-' }}
  </template>
</el-table-column>
```

在 methods 中新增辅助函数:
```javascript
getClientNames(parties) {
  if (!parties || !parties.length) return ''
  return parties
    .filter(p => p.party_type && p.party_type.includes('委托'))
    .map(p => p.name)
    .join('、')
}
```

---

### 2.13 前端 — BankCasesPage.vue

#### 2.13.1 第 136 行：表格列中的 client_name

**修改方案同上** — 改为 `<template #default>` + `getClientNames(row.parties)`。

#### 2.13.2 data() / exportForm 中的 client_name（约第 340、696、954、1024、1046 行）

**旧代码:**
```javascript
// data() 中
client_name: null,

// exportForm 中
client_name: selectedBank.value,

// 导出参数中
client_name: exportForm.client_name || null,
```

**新代码:**
```javascript
// 前端查询/导出参数中的 client_name 保持不变，
// 后端 API 收到此参数后会通过 case_parties 表进行过滤（参见 2.3.4），
// 因此前端搜索参数名无需修改。
```
> **说明**: 查询参数 `client_name` 是前端传给后端的**搜索关键词**，不是数据库字段。后端收到后通过 `CaseParty.name.like(...)` 进行查询即可，前端参数名可以保持不变。

#### 2.13.4 筛选表单中 v-model 绑定（第 340 行）

```html
<!-- 保持不变。v-model="exportForm.client_name" 是前端本地筛选参数 -->
```

---

### 2.14 前端 — CaseReviewPage.vue

#### 第 44 行：表格列中的 client_name

**旧代码:**
```html
<el-table-column prop="client_name" label="委托人" min-width="100" />
```

**新代码:**
```html
<el-table-column label="委托人" min-width="100">
  <template #default="{ row }">
    {{ getClientNames(row.parties) || '-' }}
  </template>
</el-table-column>
```

---

### 2.15 前端 — FinancePage.vue

#### 第 151–153 行：表格列中的 case.client_name

**旧代码:**
```html
<el-table-column prop="case.client_name" label="委托人" min-width="200">
  <template #default="{ row }">
    <span class="client-name">{{ row.case ? row.case.client_name : '-' }}</span>
  </template>
</el-table-column>
```

**新代码:**
```html
<el-table-column label="委托人" min-width="200">
  <template #default="{ row }">
    <span class="client-name">{{ row.case ? getClientNames(row.case.parties) : '-' }}</span>
  </template>
</el-table-column>
```

#### 第 435 行：详情展示中的 client_name

**旧代码:**
```javascript
currentFinance.case ? currentFinance.case.client_name : '-'
```

**新代码:**
```javascript
currentFinance.case ? getClientNames(currentFinance.case.parties) : '-'
```

---

### 2.16 前端 — DashBoard.vue

#### 第 493 行：紧急日程卡片中的 client_name

**旧代码:**
```javascript
<div class="urgent-client">${e.client_name ? e.client_name : e.description || '无详细备注'}</div>
```

**新代码:**
```javascript
// 后端日程事件 API 已经在 crud/case.py 中将 client_name 替换为从 CaseParty 提取的值，
// 前端无需修改，只需确认后端已改造完成。
```

> **说明**: `e.client_name` 来自后端 `/events/` API 的 JSON 响应。只要后端 CRUD 层（第 2.3.7 节）改造完成，前端此处自然正确。

---

### 2.17 前端 — EventReminderPage.vue

#### 第 301、406、410 行：案件选择器和回退逻辑

**旧代码（第 301 行）:**
```html
:label="`${item.case_number || '无案号'} - ${item.client_name || '无委托人'}`"
```

**新代码:**
```html
:label="`${item.case_number || '无案号'} - ${(item.client_name || '') || '无委托人'}`"
<!-- 保持不变，item.client_name 来自后端 API 响应，后端已完成改造 -->
```

**旧代码（第 406、410 行）:**
```javascript
if (row.client_name) return row.client_name
// ...
if (matched) return matched.client_name || '--'
```

**新代码:**
```javascript
// 保持不变，数据源自后端 API，后端已经改造。
```

---

### 2.18 BankCaseForm.vue 和 GeneralCaseForm.vue

这两个文件中的 `party_plaintiffs`、`party_defendants` 引用属于**新的 case_parties 表结构**，并非废弃字段引用。CSS 中的 `.plaintiff-card`、`.defendant-card` 类名同理，无需修改。

唯一需要清理的是：如果这两个文件中有引用 `formData.client_name`、`formData.plaintiff`、`formData.defendant` 等旧字段名，请按 CaseForm.vue 的模式删除。

---

## 三、数据库清理 SQL

> **执行前务必对数据库进行完整备份！**

```sql
-- ============================================================
-- 案件当事人字段废弃 — 数据库清理脚本
-- 数据库: MySQL
-- 表名: cases
-- 说明: 删除已迁移至 case_parties 表的 8 个废弃字段
-- 日期: 2026-05-25
-- ============================================================

-- 请先确认 case_parties 表中已包含所有历史数据：
-- SELECT COUNT(*) FROM case_parties;
-- SELECT COUNT(*) FROM cases WHERE client_name IS NOT NULL AND client_name != '';

ALTER TABLE `cases`
    DROP COLUMN IF EXISTS `client_name`,
    DROP COLUMN IF EXISTS `client_id_number`,
    DROP COLUMN IF EXISTS `client_phone`,
    DROP COLUMN IF EXISTS `plaintiff`,
    DROP COLUMN IF EXISTS `appellant_info`,
    DROP COLUMN IF EXISTS `extra_appellant_info`,
    DROP COLUMN IF EXISTS `defendant`,
    DROP COLUMN IF EXISTS `third_party`;

-- 验证删除结果
-- DESCRIBE `cases`;
-- 确认以上 8 个字段已不在表结构中。
```

**执行删除操作前，请务必先对数据库进行完整备份。**
