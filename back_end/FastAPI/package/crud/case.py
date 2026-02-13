# crud/case.py
from datetime import datetime
from typing import List, Optional, cast

from sqlalchemy import func, or_, extract
from sqlalchemy.orm import Session, joinedload

from ..models.case import Case,BankCase,CaseParty
from ..models.finance import CaseFinance
from ..schemas.case import CaseCreate, CaseUpdate


def get_case_by_id(db: Session, case_id: int) -> Optional[Case]:
    """
    根据案件ID获取案件
    """
    return (
        db.query(Case)
        .options(
            joinedload(Case.main_lawyer),
            joinedload(Case.assistant_lawyer),
            joinedload(Case.execution_lawyer),
            joinedload(Case.execution_assistant),
            joinedload(Case.bank_case_details),
        )
        .filter(
            Case.case_id == case_id,
            Case.is_deleted == False
        )
        .first()
    )

def list_cases_by_user_role(
    db: Session,
    user_id: int,
    role: str,
    skip: int = 0,
    limit: int = 100,
    keyword: Optional[str] = None,  # 关键词查询
    category: Optional[str] = None,  # 案件类型筛选
    main_lawyer_id: Optional[int] = None,    # 主办律师筛选
    year: Optional[str] = None,  # 年份筛选
    sort_field: str = "created_at",  # 排序字段，默认按创建时间
    sort_dir: str = "desc"  # 排序方向，默认降序（最新在前）
) -> List[Case]:
    """
    根据用户角色返回案件列表
    - 普通用户：只能看到自己为主办律师或协办律师的案件
    - admin/owner：可以看到全部案件
    """
    query = db.query(Case).options(
        joinedload(Case.main_lawyer),
        joinedload(Case.assistant_lawyer),
        joinedload(Case.execution_lawyer),
        joinedload(Case.execution_assistant),
    ).filter(Case.is_deleted == False)

    if year:
        # 使用 extract 提取委托日期的年份进行匹配
        query = query.filter(extract('year', Case.commission_date) == year)

    # 角色与主办律师筛选逻辑
    if role not in ["admin", "owner"]:
        # 普通律师：只能看到自己相关的案件
        query = query.filter(
            or_(
                Case.main_lawyer_id == user_id,
                Case.assistant_lawyer_id == user_id
            )
        )
    else:
        # 管理员/所有者：默认看全部，但如果选择了特定律师，则进行过滤
        if main_lawyer_id is not None:
            query = query.filter(Case.main_lawyer_id == main_lawyer_id)

    # 类别筛选
    if category:
        query = query.filter(Case.case_category == category)

    # 关键词搜索
    if keyword:
        query = query.filter(
            (Case.case_number.like(f"%{keyword}%")) |
            (Case.client_name.like(f"%{keyword}%"))
        )

    # 排序逻辑
    if sort_field == "created_at":
        order_column = Case.created_at
    elif sort_field == "updated_at":
        order_column = Case.updated_at
    elif sort_field == "commission_date":  # 委托日期
        order_column = Case.commission_date
    else:
        order_column = Case.created_at  # 默认字段

    if sort_dir == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())

    cases = query.offset(skip).limit(limit).all()
    return cast(list[Case], cast(object, cases))

def count_cases_by_user_role(
    db: Session,
    user_id: int,
    role: str,
    keyword: Optional[str] = None,  # 关键词查询
    category: Optional[str] = None,  # 案件类型筛选
    main_lawyer_id: Optional[int] = None,  # 主办律师筛选
    year: Optional[str] = None  #  年份筛选
) -> int:
    """
    根据用户角色统计案件总数
    """
    query = db.query(Case).filter(Case.is_deleted == False)
    if year:
        query = query.filter(extract('year', Case.commission_date) == year)

    # 角色筛选
    if role not in ["admin", "owner"]:
        query = query.filter(
            or_(
                Case.main_lawyer_id == user_id,
                Case.assistant_lawyer_id == user_id
            )
        )
    else:
        # 管理员可以筛选特定主办律师
        if main_lawyer_id is not None:
            query = query.filter(Case.main_lawyer_id == main_lawyer_id)

    # 类别筛选
    if category:
        query = query.filter(Case.case_category == category)

    # 关键词搜索
    if keyword:
        query = query.filter(
            (Case.case_number.like(f"%{keyword}%")) |
            (Case.client_name.like(f"%{keyword}%"))
        )

    return query.count()

def list_bank_cases_by_user_role(
    db: Session,
    user_id: int,
    role: str,
    skip: int = 0,
    limit: int = 100,
    keyword: Optional[str] = None,  # 新增
    main_lawyer_id: Optional[int] = None,    # 主办律师筛选
    sort_field: str = "created_at",  # 排序字段，默认按创建时间
    sort_dir: str = "desc"  # 排序方向，默认降序（最新在前）
) -> List[Case]:
    """
    根据用户角色返回银行案件列表
    - 普通用户：只能看到自己为主办律师或协办的案件
    - admin/owner：可以看到全部案件
    """
    query = db.query(Case).options(
        joinedload(Case.main_lawyer),
        joinedload(Case.assistant_lawyer),
        joinedload(Case.execution_lawyer),
        joinedload(Case.execution_assistant),
    ).filter(Case.is_deleted == False,Case.case_category == "银行案件")

    # 角色筛选
    if role not in ["admin", "owner"]:
        query = query.filter(
            or_(
                Case.main_lawyer_id == user_id,
                Case.assistant_lawyer_id == user_id
            )
        )
    else:
        # 管理员可以筛选特定主办律师
        if main_lawyer_id is not None:
            query = query.filter(Case.main_lawyer_id == main_lawyer_id)

    # 关键词搜索（案件号或委托人）
    if keyword:
        query = query.filter(
            (Case.case_number.like(f"%{keyword}%")) |
            (Case.client_name.like(f"%{keyword}%"))
        )

    # 排序逻辑
    if sort_field == "created_at":
        order_column = Case.created_at
    elif sort_field == "updated_at":
        order_column = Case.updated_at
    elif sort_field == "commission_date":  # 委托日期
        order_column = Case.commission_date
    else:
        order_column = Case.created_at  # 默认字段

    if sort_dir == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())

    cases = query.offset(skip).limit(limit).all()
    return cast(list[Case], cast(object, cases))

def count_bank_cases_by_user_role(
    db: Session,
    user_id: int,
    role: str,
    keyword: Optional[str] = None,  # 新增
    main_lawyer_id: Optional[int] = None
) -> int:
    """
    根据用户角色统计案件总数
    """
    query = db.query(Case).filter(Case.is_deleted == False,Case.case_category == "银行案件")
    # 角色筛选
    if role not in ["admin", "owner"]:
        query = query.filter(
            or_(
                Case.main_lawyer_id == user_id,
                Case.assistant_lawyer_id == user_id
            )
        )
    else:
        # 管理员可以筛选特定主办律师
        if main_lawyer_id is not None:
            query = query.filter(Case.main_lawyer_id == main_lawyer_id)

    # 关键词搜索
    if keyword:
        query = query.filter(
            (Case.case_number.like(f"%{keyword}%")) |
            (Case.client_name.like(f"%{keyword}%"))
        )

    return query.count()


# 辅助函数：将当事人列表转换为逗号分隔字符串（用于兼容旧字段）
def _sync_legacy_fields(parties_data: list) -> dict:
    clients = []
    plaintiffs = []
    defendants = []
    for p in parties_data:
        # 这里需要判断 p 是对象还是字典，取决于传入来源
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

    # 额外逻辑：如果存在委托人，将第一个委托人的电话和身份证同步到主表
    if clients:
        first_client = clients[0]
        # 兼容字典和对象
        phone = first_client.phone if hasattr(first_client, 'phone') else first_client.get('phone')
        id_number = first_client.id_number if hasattr(first_client, 'id_number') else first_client.get('id_number')

        result["client_phone"] = phone
        result["client_id_number"] = id_number

    return result


def create_case(db: Session, case_in: CaseCreate) -> Case:
    """
    创建新案件（复用已删除案件的原始编号，但创建新记录）
    """
    year = datetime.now().year

    # 案件类型映射
    type_map = {
        "民事案件": "民字",
        "刑事案件": "刑字",
        "仲裁案件": "仲字",
        "行政案件": "行字",
        "非诉业务": "非诉字",
        "法律顾问业务": "法顾字",
        "银行案件": "银行案件",
        "法律援助(民事)": "法律援助(民)",
        "法律援助(刑事)": "法律援助(刑)",
        "法律援助(行政)": "法律援助(行)",
    }

    case_type = case_in.case_category
    if case_type not in type_map:
        raise ValueError("未知的案件类型")

    # 第一步：查找可复用的已删除案件编号
    available_case_number = _find_reusable_case_number(db, case_type, year)

    # 创建全新的案件记录，但使用复用的编号
    # 分离 Case 数据和 BankCase、parties 数据
    case_data = case_in.model_dump(exclude={"bank_details", "parties"})

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

    # 创建主案件
    case_data["review_status"] = "待审核"
    case_data["is_deleted"] = False
    new_case = Case(**case_data, case_number=available_case_number)
    db.add(new_case)
    db.flush()  # 刷新以获取 new_case.case_id

    # 案件创建时，自动建立一对一的财务关联，初始金额为0
    new_finance = CaseFinance(
        case_id=new_case.case_id,
        contract_amount=0,  # 初始为0，由财务后续修改
        remarks="案件创建自动初始化"
    )
    db.add(new_finance)

    # 保存当事人列表
    if case_in.parties:
        for party in case_in.parties:
            new_party = CaseParty(
                case_id=new_case.case_id,
                **party.model_dump()
            )
            db.add(new_party)

    # 如果是银行案件且提供了详情，则创建扩展表记录
    if case_in.case_category == "银行案件" and case_in.bank_details:
        bank_data = case_in.bank_details.model_dump()
        new_bank_case = BankCase(case_id=new_case.case_id, **bank_data)
        db.add(new_bank_case)

    db.commit()
    db.refresh(new_case)
    return new_case


def _find_reusable_case_number(db: Session, case_type: str, year: int) -> str:
    """
    查找可复用的案件编号
    """
    type_map = {
        "民事案件": "民字",
        "刑事案件": "刑字",
        "仲裁案件": "仲字",
        "行政案件": "行字",
        "非诉业务": "非诉字",
        "法律顾问业务": "法顾字",
        "银行案件": "银行案件",
        "法律援助(民事)": "法律援助(民)",
        "法律援助(刑事)": "法律援助(刑)",
        "法律援助(行政)": "法律援助(行)",
    }

    # 查找已删除的案件，按案件号排序（找到最小的可用编号）
    deleted_cases = db.query(Case).filter(
        Case.case_category == case_type,
        Case.is_deleted == True,
        Case.case_number.like(f"[已删除]湘生律({year})%")
    ).order_by(Case.case_number).all()

    # 优先复用已删除案件的原始编号
    for deleted_case in deleted_cases:
        original_number = deleted_case.case_number.replace("[已删除]", "").split("-ID")[0]

        # 检查这个原始编号是否已被其他活跃案件使用
        existing_active_case = db.query(Case).filter(
            Case.case_number == original_number,
            Case.is_deleted == False
        ).first()

        if not existing_active_case:
            # 这个编号可用，直接返回
            return original_number

    # 如果没有可复用的编号，创建新编号
    return _create_new_case_number(db, case_type, year, type_map)


def _create_new_case_number(db: Session, case_type: str, year: int, type_map: dict) -> str:
    """
    创建新案件编号（修复版：解决ID顺序与案号顺序不一致导致的冲突）
    """
    # 尝试基于最新ID的案件推算（但这不一定是最大案号）
    latest_case = db.query(Case).filter(
        Case.case_category == case_type,
        Case.case_number.like(f"湘生律({year})%")
        # 去掉 is_deleted 限制，确保基于所有历史数据递增
    ).order_by(Case.case_id.desc()).first()

    next_number = 1
    if latest_case:
        try:
            # 提取数字
            if "第" in latest_case.case_number and "号" in latest_case.case_number:
                last_number = int(latest_case.case_number.split("第")[-1].replace("号", ""))
                next_number = last_number + 1
        except (ValueError, IndexError):
            next_number = 1

    # 循环检测，直到找到一个真正空闲的号码
    while True:
        candidate = f"湘生律({year}){type_map[case_type]}第{next_number}号"

        # 检查候选号码是否已存在（包含已删除但未改名的）
        exists = db.query(Case).filter(Case.case_number == candidate).first()

        if not exists:
            return candidate

        # 如果存在，递增序号并重试
        next_number += 1


def update_case(db: Session, case_id: int, case_in: CaseUpdate) -> Optional[Case]:
    """
    更新已有案件
    """
    case = db.query(Case).options(
        joinedload(Case.main_lawyer),
        joinedload(Case.assistant_lawyer),
        joinedload(Case.execution_lawyer),
        joinedload(Case.execution_assistant),
        joinedload(Case.bank_case_details),
    ).filter(
        Case.case_id == case_id,
        Case.is_deleted == False
    ).first()

    if not case:
        return None

    # 保存旧类型，提取新类型（注意可能未传入新类型）
    old_category = case.case_category
    new_category = case_in.case_category or old_category

    # 检查是否修改了案件类别
    category_changed = (new_category != old_category)


    # 更新主表数据
    # 先批量更新其他字段，但跳过案件类别，避免提前改变
    case_data = case_in.model_dump(exclude_unset=True, exclude={"bank_details", "parties"})
    for key, value in case_data.items():
        if key == "case_category": continue
        setattr(case, key, value)

    # 处理当事人列表更新 (全删全增策略)
    if case_in.parties is not None:
        # A. 删除该案件所有的旧当事人
        db.query(CaseParty).filter(CaseParty.case_id == case_id).delete()

        # B. 添加新当事人
        for party in case_in.parties:
            new_party = CaseParty(
                case_id=case_id,
                **party.model_dump()
            )
            db.add(new_party)

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

    # 更新或创建银行案件详情
    if case_in.bank_details:
        if case.bank_case_details:
            # 更新现有记录
            bank_update_data = case_in.bank_details.model_dump(exclude_unset=True)
            for k, v in bank_update_data.items():
                setattr(case.bank_case_details, k, v)
        else:
            # 如果之前没有详情（可能是从其他类型转过来的），则创建
            if case.case_category == "银行案件":
                bank_data = case_in.bank_details.model_dump()
                new_bank_case = BankCase(case_id=case.case_id, **bank_data)
                db.add(new_bank_case)

    # 如果案件类别发生变化，则重新生成编号
    if category_changed:
        year = datetime.now().year
        type_map = {
            "民事案件": "民字",
            "刑事案件": "刑字",
            "仲裁案件": "仲字",
            "行政案件": "行字",
            "非诉业务": "非诉字",
            "法律顾问业务": "法顾字",
            "银行案件": "银行案件",
            "法律援助(民事)": "法律援助(民)",
            "法律援助(刑事)": "法律援助(刑)",
            "法律援助(行政)": "法律援助(行)",
        }

        if new_category not in type_map:
            raise ValueError("未知的案件类型")

        # 查询该类型最新案件号
        latest_case = db.query(Case).filter(
            Case.case_category == new_category,
            Case.case_number.like(f"湘生律({year})%")
        ).order_by(Case.case_id.desc()).first()

        next_number = 1
        if latest_case:
            try:
                last_number = int(latest_case.case_number.split("第")[-1].replace("号", ""))
                next_number = last_number + 1
            except ValueError:
                next_number = 1  # 容错处理

        # 生成新编号并更新类型
        case.case_category = new_category
        case.case_number = f"湘生律({year}){type_map[new_category]}第{next_number}号"

        # 如果案件类型发生变更，统一设置为待审核,并将审核人设为空
        case.review_status = "待审核"
        case.reviewer_id = None

    db.commit()
    db.refresh(case)
    return cast(Case, case)


def delete_case(db: Session, case_id: int) -> bool:
    """
    删除案件（逻辑删除）
    """
    case = db.query(Case).filter(Case.case_id == case_id, Case.is_deleted == False).first()
    if not case:
        return False

    # 在案件号前添加删除标记和唯一ID
    if not case.case_number.startswith("[已删除]"):
        case.case_number = f"[已删除]{case.case_number}-ID{case_id}"

    case.is_deleted = True
    db.commit()
    return True


def list_cases_by_lawyer(db: Session, lawyer_id: int) -> List[Case]:
    """
    获取指定律师相关的案件（主办/助理/执行律师/执行助理）
    """
    return cast(
        List[Case],
        cast(object, db.query(Case)
             .options(
            joinedload(Case.main_lawyer),
            joinedload(Case.assistant_lawyer),
            joinedload(Case.execution_lawyer),
            joinedload(Case.execution_assistant),
        )
             .filter(
            Case.is_deleted == False,
            (
                    (Case.main_lawyer_id == lawyer_id)
                    | (Case.assistant_lawyer_id == lawyer_id)
                    | (Case.execution_lawyer_id == lawyer_id)
                    | (Case.execution_assistant_id == lawyer_id)
            )
        )
             .all()),
    )

# 导出数据查询
def export_cases_by_user_role(
        db: Session,
        user_id: int,
        role: str
) -> List[Case]:
    """查询符合条件的所有案件（无分页）"""
    query = db.query(Case).filter()

    # 权限过滤
    if role not in ["admin", "owner"]:
        query = query.filter(or_(
                Case.main_lawyer_id == user_id,
                Case.assistant_lawyer_id == user_id
            ),Case.is_deleted == False)

    return cast(list[Case], cast(object, query.all()))

def export_bank_cases_by_user_role(
        db: Session,
        user_id: int,
        role: str
) -> List[Case]:
    """查询符合条件的所有案件（无分页）"""
    query = db.query(Case).filter(Case.case_category == "银行案件")

    # 权限过滤
    if role not in ["admin", "owner"]:
        query = query.filter(or_(
                Case.main_lawyer_id == user_id,
                Case.assistant_lawyer_id == user_id
            ),Case.is_deleted == False)

    return cast(list[Case], cast(object, query.all()))

def count_main_cases(db: Session, lawyer_id: int, year: Optional[int] = None) -> int:
    """统计主办案件数量"""
    query = db.query(Case).filter(Case.main_lawyer_id == lawyer_id, Case.is_deleted == False)
    if year:
        query = query.filter(func.extract('year', Case.commission_date) == year)
    return query.count()


def sum_main_case_income(db: Session, lawyer_id: int, year: Optional[int] = None) -> float:
    """统计主办案件总收费"""
    query = db.query(func.sum(Case.case_income)).filter(Case.main_lawyer_id == lawyer_id, Case.is_deleted == False)
    if year:
        query = query.filter(func.extract('year', Case.commission_date) == year)
    result = query.first()
    return result[0] or 0


def count_cases_by_category(db: Session, lawyer_id: int, year: Optional[int] = None) -> dict:
    """按案件类型统计数量"""
    query = db.query(Case.case_category, func.count(Case.case_id)). \
        filter(Case.main_lawyer_id == lawyer_id, Case.is_deleted == False)

    if year:
        query = query.filter(func.extract('year', Case.commission_date) == year)

    categories = query.group_by(Case.case_category).all()
    return {category: count for category, count in categories}

# 拆分字符串工具
def split_with_separators(s: str, separators: list) -> list:
    """按多个分隔符拆分字符串"""
    import re
    # 构建正则表达式：匹配任何分隔符
    separator_pattern = '|'.join(re.escape(sep) for sep in separators)
    return re.split(separator_pattern, s)


# 事件提醒功能
def get_upcoming_events(db: Session, user_id: int, days: int = 30) -> List[dict]:
    """
    查询用户（主办或助理）未来 X 天内的关键事项
    """
    from datetime import date, timedelta

    today = date.today()
    target_date = today + timedelta(days=days)

    # 1. 查询该律师相关的所有未删除、未归档(可选)的案件
    # 这里假设 '已结案' 的案件不需要提醒，或者根据实际需求调整
    cases = db.query(Case).filter(
        Case.is_deleted == False,
        or_(
            Case.main_lawyer_id == user_id,
            Case.assistant_lawyer_id == user_id
        )
    ).all()

    events = []

    for case in cases:
        # 定义需要检查的字段映射
        check_points = [
            ("开庭", case.hearing_date),
            ("保全到期", case.preservation_end),
            ("调解到期", case.mediation_due_date),
            ("执行到期", case.execution_due_date),
            ("付款到期", case.payment_due_date)
        ]

        for event_type, event_date in check_points:
            if event_date:
                # 检查日期是否在 [今天, 目标日期] 范围内
                # 注意：如果是保全到期，通常建议包含今天之前已过期的（作为警告），这里仅演示未来提醒
                if today <= event_date <= target_date:
                    days_remaining = (event_date - today).days
                    events.append({
                        "case_id": case.case_id,
                        "case_number": case.case_number,
                        "client_name": case.client_name,
                        "event_type": event_type,
                        "event_date": event_date,
                        "days_remaining": days_remaining
                    })

    # 按剩余天数排序，紧迫的在前
    events.sort(key=lambda x: x['days_remaining'])
    return events