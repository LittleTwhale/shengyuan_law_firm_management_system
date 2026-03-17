# crud/case.py
import json
import os
from datetime import datetime
from io import BytesIO
from typing import List
from typing import Optional, cast

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from sqlalchemy import func
from sqlalchemy import or_, extract
from sqlalchemy.orm import Session, joinedload

from ..models.case import Case, CaseParty, BankCase
from ..models.electronic_volume_model import CaseVolume, VolumeFile
from ..models.finance_model import CaseFinance
from ..schemas.case import CaseCreate, CaseUpdate
from ..schemas.case import CaseExportQuery


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
    year: Optional[str] = None,
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
    # 委托年份筛选
    if year:
        query = query.filter(extract('year', Case.commission_date) == year)

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
    main_lawyer_id: Optional[int] = None,
    year: Optional[str] = None
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

    # 委托年份筛选
    if year:
        query = query.filter(extract('year', Case.commission_date) == year)

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
        "劳动仲裁": "劳仲字",
        "商事仲裁": "商仲字",
        "行政案件": "行字",
        "非诉业务": "非诉字",
        "执行案件": "执行字",
        "法律顾问业务": "法顾字",
        "银行案件": "银行案件",
        "法律援助(民事)": "法律援助(民)",
        "法律援助(刑事)": "法律援助(刑)",
        "法律援助(行政)": "法律援助(行)",
    }

    case_type = case_in.case_category
    if case_type not in type_map:
        raise ValueError("未知的案件类型")

    if case_in.case_number:
        # 校验手动传入的案件号是否已存在，防止触发 models 中 case_number unique=True 的报错
        existing_case = db.query(Case).filter(Case.case_number == case_in.case_number).first()
        if existing_case:
            raise ValueError(f"案件号 {case_in.case_number} 已存在，请检查导入表格")
        final_case_number = case_in.case_number
    else:
        # 如果没有传入案件号，执行原有的自动生成逻辑
        final_case_number = _find_reusable_case_number(db, case_type, year)

    # 清洗当事人列表空字段
    if case_in.parties:
        for party in case_in.parties:
            for key, value in party.model_dump().items():
                if isinstance(value, str) and value.strip() in ("None", "nan", "NaN", "", "null"):
                    # 使用 setattr 修改 Pydantic 对象的属性，而不是 party[key]
                    setattr(party, key, None)

    # 创建全新的案件记录，但使用复用的编号
    # 分离 Case 数据和 BankCase、parties 数据
    case_data = case_in.model_dump(exclude={"bank_case_details", "parties", "case_number"})

    # 清洗数据，将字面量字符串 "None", "nan", "" 转换为真正的 None
    for key, value in case_data.items():
        if isinstance(value, str):
            # 去除首尾空格后，如果是这些无效值，就转为 None
            if value.strip() in ("None", "nan", "NaN", "", "null"):
                case_data[key] = None

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
    new_case = Case(**case_data, case_number=final_case_number)
    db.add(new_case)
    db.flush()  # 刷新以获取 new_case.case_id

    # 案件创建时，自动建立一对一的财务关联
    initial_amount = new_case.case_income or 0
    new_finance = CaseFinance(
        case_id=new_case.case_id,
        contract_amount=initial_amount,
        unpaid_amount=initial_amount,  # 初始欠款直接等于合同金额
        uninvoiced_amount=initial_amount,  # 初始未开票直接等于合同金额
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
    if case_in.case_category == "银行案件" and case_in.bank_case_details:
        bank_data = case_in.bank_case_details.model_dump()
        # 清洗银行案件中的字符串 "None"
        for key, value in bank_data.items():
            if isinstance(value, str) and value.strip() in ("None", "nan", "NaN", "", "null"):
                bank_data[key] = None
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
        "劳动仲裁": "劳仲字",
        "商事仲裁": "商仲字",
        "行政案件": "行字",
        "非诉业务": "非诉字",
        "执行案件": "执行字",
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
    case_data = case_in.model_dump(exclude_unset=True, exclude={"bank_case_details", "parties"})
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
    if case_in.bank_case_details:
        if case.bank_case_details:
            # 更新现有记录
            bank_update_data = case_in.bank_case_details.model_dump(exclude_unset=True)
            for k, v in bank_update_data.items():
                setattr(case.bank_case_details, k, v)
        else:
            # 如果之前没有详情（可能是从其他类型转过来的），则创建
            if case.case_category == "银行案件":
                bank_data = case_in.bank_case_details.model_dump()
                new_bank_case = BankCase(case_id=case.case_id, **bank_data)
                db.add(new_bank_case)

    # 如果案件类别发生变化，则重新生成编号
    if category_changed:
        year = datetime.now().year
        type_map = {
            "民事案件": "民字",
            "刑事案件": "刑字",
            "劳动仲裁": "劳仲字",
            "商事仲裁": "商仲字",
            "行政案件": "行字",
            "非诉业务": "非诉字",
            "执行案件": "执行字",
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
    删除案件（逻辑删除 Case，但在物理上清理关联的卷宗文件和财务数据）
    """
    case = db.query(Case).filter(Case.case_id == case_id, Case.is_deleted == False).first()
    if not case:
        return False

    # =========================================================
    # 1. 清理电子卷宗 (数据库记录 + 物理文件)
    # =========================================================
    # 查询该案件下的所有卷册
    volumes = db.query(CaseVolume).filter(CaseVolume.case_id == case_id).all()

    for volume in volumes:
        # A. 删除卷册合并的 PDF (如果有)
        if volume.merged_file_path and os.path.exists(volume.merged_file_path):
            try:
                os.remove(volume.merged_file_path)
            except OSError as e:
                print(f"删除合并卷宗文件失败: {e}")

        # B. 删除卷内文件
        # 注意：这里需要查询 VolumeFile，因为 CaseVolume 和 VolumeFile 配置了 cascade，
        # 直接 db.delete(volume) 会删数据库记录，但不会删磁盘文件，所以我们要手动遍历。
        files = db.query(VolumeFile).filter(VolumeFile.volume_id == volume.id).all()
        for file_obj in files:
            if file_obj.file_path and os.path.exists(file_obj.file_path):
                try:
                    os.remove(file_obj.file_path)
                except OSError as e:
                    print(f"删除物理文件失败: {file_obj.file_path}, 错误: {e}")

            # 手动删除文件记录 (或者依赖 volume 的 cascade)
            db.delete(file_obj)

        # C. 删除卷册记录
        db.delete(volume)

    # =========================================================
    # 2. 清理财务数据
    # =========================================================
    if case.finance:
        # 由于你在 finance_model.py 中配置了 cascade="all, delete-orphan"
        # 删除 CaseFinance 会自动级联删除 Records, Invoices, Withdrawals
        db.delete(case.finance)

    # =========================================================
    # 3. 案件本身的逻辑删除处理 (原逻辑)
    # =========================================================
    # 在案件号前添加删除标记和唯一ID，防止将来复用案号冲突
    if not case.case_number.startswith("[已删除]"):
        case.case_number = f"[已删除]{case.case_number}-ID{case_id}"

    case.is_deleted = True

    # 提交事务
    # SQLAlchemy 会在一个事务中执行上述所有的 delete 和 update
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
    from sqlalchemy.orm import joinedload # 引入 joinedload 以优化查询

    today = date.today()
    # 只有 days > 0 时才需要计算目标日期
    if days > 0:
        target_date = today + timedelta(days=days)

    # 1. 查询该律师相关的所有未删除、未归档(可选)的案件
    cases = db.query(Case).options(
        joinedload(Case.bank_case_details)
    ).filter(
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
            ("付款到期", case.payment_due_date),
            ("顾问到期", case.advisory_due_date),
        ]

        # ========== 将银行案件的诉讼时效加入检查点 ==========
        if case.case_category == "银行案件" and case.bank_case_details:
            check_points.append(("诉讼时效到期", case.bank_case_details.statute_of_limitations))
        # ==========================================================

        for event_type, event_date in check_points:
            if event_date:
                # 检查日期是否符合条件：
                # 1. 如果 days == 0，表示查询全部未来的待办（只限制大于等于今天即可）
                # 2. 如果 days > 0，表示查询 [今天, 目标日期] 范围内的待办
                if (days == 0 and event_date >= today) or (days > 0 and today <= event_date <= target_date):
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


def export_cases_to_excel(db: Session, user_id: int, role: str, query_params: CaseExportQuery) -> BytesIO:
    """
    导出业务数据为Excel文件 (主表看概况 + 子表查详情)
    """
    # 1. 基础查询与预加载
    query = db.query(Case).options(
        joinedload(Case.main_lawyer),
        joinedload(Case.assistant_lawyer),
        joinedload(Case.execution_lawyer),
        joinedload(Case.execution_assistant),
        joinedload(Case.reviewer),
        joinedload(Case.parties),
        joinedload(Case.bank_case_details)
    ).filter(Case.is_deleted == False)

    # 权限控制
    if role not in ["admin", "owner"]:
        query = query.filter(
            or_(
                Case.main_lawyer_id == user_id,
                Case.assistant_lawyer_id == user_id,
                Case.execution_lawyer_id == user_id,
                Case.execution_assistant_id == user_id
            )
        )

    # 2. 动态筛选条件
    if query_params.keyword:
        query = query.filter(
            or_(
                Case.case_number.like(f"%{query_params.keyword}%"),
                Case.client_name.like(f"%{query_params.keyword}%")
            )
        )
    if query_params.case_category:
        query = query.filter(Case.case_category == query_params.case_category)
    if query_params.main_lawyer_id:
        query = query.filter(Case.main_lawyer_id == query_params.main_lawyer_id)

    # 时间筛选逻辑：只有未传入起止日期才对年份进行筛选
    if query_params.start_date or query_params.end_date:
        if query_params.start_date:
            query = query.filter(Case.commission_date >= query_params.start_date)
        if query_params.end_date:
            query = query.filter(Case.commission_date <= query_params.end_date)
    elif query_params.year:
        query = query.filter(extract('year', Case.commission_date) == query_params.year)

    # 按照创建时间倒序获取所有数据
    cases = query.order_by(Case.created_at.desc()).all()

    # 3. 创建 Excel 及 Sheet (动态生成)
    wb = Workbook()

    # 移除默认的空Sheet，防止出现多余的空标签页
    if "Sheet" in wb.sheetnames:
        wb.remove(wb["Sheet"])

    ws_standard = None
    ws_bank = None

    # 根据筛选条件决定需要生成哪些主表Sheet
    if query_params.case_category == "银行案件":
        ws_bank = wb.create_sheet(title="银行案件")
    elif query_params.case_category and query_params.case_category != "银行案件":
        ws_standard = wb.create_sheet(title="常规业务")
    else:
        # 没有指定类型（导出全部），两个主表Sheet都生成
        ws_standard = wb.create_sheet(title="常规业务")
        ws_bank = wb.create_sheet(title="银行案件")

    # --- 新增：创建独立的当事人明细 Sheet ---
    ws_parties = wb.create_sheet(title="当事人明细")

    # ---------------- 表头定义 ----------------
    base_headers_part1 = ["业务ID", "业务号", "委托日期", "业务类别"]

    # 拆分当事人列头 (扩展电话和身份证)
    party_headers = [
        "委托人", "委托人联系电话", "委托人证件号",
        "原告/申请人/上诉人", "原告/申请人/上诉人联系电话", "原告/申请人/上诉人证件号",
        "被告(人)/被申请人/被上诉人", "被告(人)/被申请人/被上诉人联系电话", "被告(人)/被申请人/被上诉人证件号",
        "第三人", "第三人联系电话", "第三人证件号",
        "其他当事人", "其他当事人联系电话", "其他当事人证件号"
    ]

    base_headers_part2 = [
        "案件来源", "收费方式", "风险比例", "案件收入",
        "付款到期日", "案由", "介入阶段", "代理权限", "审理法院", "侦查机关", "检察院", "二审检察机关", "开庭时间",
        "立案日", "结案时间",
        "案件地点", "案件详情", "主办律师", "助理律师", "执行主办律师", "执行助理律师", "审核状态", "审核人",
        "是否重大", "是否纸质卷宗", "是否解除", "是否笔录", "是否保全", "保全开始日", "保全终止日",
        "案号", "结案状态", "结案方式", "诉讼费缴费时间", "诉讼费缴费金额", "诉讼费退费时间", "诉讼费退费金额",
        "申请执行日", "调解到期日", "执行到期日", "顾问到期日", "创建时间", "更新时间"
    ]

    # 银行案件特有字段 (BankCase)
    bank_specific_headers = [
        "支行名称", "案件状态", "银行要求案件状态", "缺少具体材料", "抵/质押物信息", "抵押物位置", "客户经理",
        "贷款类型", "贷款账号",
        "贷款本金", "诉讼标的金额(含利息)", "信用卡违约金", "借款日", "到期日", "诉讼时效", "收案日期",
        "取材料人", "诉前催收情况", "盖章日", "材料提交法院日", "承办法官", "裁判时间", "裁判方式",
        "裁判摘要", "支持律师费金额", "被告支付律师费金额", "是否还清", "是否有二审/再审",
        "执行案号", "执行立案时间", "执行法官", "借款人工作单位", "是否为恢复执行", "收取执行材料时间",
        "执行材料提交法院时间", "执行本金金额", "执行律师费金额", "财产调查情况", "网络查控财产情况",
        "承办人执行方案", "法院执行措施", "查封冻结时间", "拍卖程序", "拍卖变卖成交价",
        "执行和解内容", "终本时间", "终本原因", "终结执行时间", "恢复执行时间", "还清时间",
        "执行回款总金额", "执行回款来源", "执行和解跟进及回款额", "扣划跟进及回款额", "调解案件履行跟踪情况"
    ]

    party_detail_headers = [
        "关联业务号", "业务类别", "当事人名称", "类型",
        "法定代表人", "身份证号/统一社会信用代码", "联系电话", "联系地址"
    ]

    # 组合表头写入
    if ws_standard:
        ws_standard.append(base_headers_part1 + party_headers + base_headers_part2)
    if ws_bank:
        ws_bank.append(base_headers_part1 + party_headers + base_headers_part2 + bank_specific_headers)

    ws_parties.append(party_detail_headers)

    # 设置表头样式
    for ws in [ws for ws in [ws_standard, ws_bank, ws_parties] if ws is not None]:
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center")

    # ---------------- 辅助函数 ----------------
    def format_date(d):
        return d.strftime("%Y-%m-%d") if d else ""

    def format_datetime(dt):
        return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""

    def format_bool(b):
        return "是" if b else "否"

    def format_decimal(d):
        return float(d) if d is not None else 0.0

    def format_json(j):
        if not j: return ""
        try:
            return json.dumps(j, ensure_ascii=False)
        except:
            return str(j)

    # ---------------- 填充数据 ----------------
    for case in cases:
        # 初始化分类当事人信息列表：(姓名, 电话, 证件号)
        clients_name, clients_phone, clients_id = [], [], []
        plaintiffs_name, plaintiffs_phone, plaintiffs_id = [], [], []
        defendants_name, defendants_phone, defendants_id = [], [], []
        thirds_name, thirds_phone, thirds_id = [], [], []
        others_name, others_phone, others_id = [], [], []

        # 遍历当事人，分发数据
        if case.parties:
            for p in case.parties:
                # 1. 写入子表 (当事人明细)
                ws_parties.append([
                    case.case_number or "",
                    case.case_category or "",
                    p.name or "",
                    p.party_type or "",
                    p.legal_representative or "",
                    p.id_number or "",
                    p.phone or "",
                    p.address or ""
                ])

                # 2. 为主表聚合字符串 (按角色分组)
                ptype = p.party_type or ""
                pname = p.name or "未知姓名"

                # 提取电话和证件号，如果为空则用 "-" 占位，保证换行对齐
                p_phone = p.phone or "-"
                p_id = p.id_number or "-"

                if "委托人" in ptype:
                    clients_name.append(pname)
                    clients_phone.append(p_phone)
                    clients_id.append(p_id)
                elif ptype in ["原告", "申请人", "上诉人"]:
                    plaintiffs_name.append(pname)
                    plaintiffs_phone.append(p_phone)
                    plaintiffs_id.append(p_id)
                elif ptype in ["被告", "被告人", "被申请人", "被上诉人"]:
                    defendants_name.append(pname)
                    defendants_phone.append(p_phone)
                    defendants_id.append(p_id)
                elif ptype == "第三人":
                    thirds_name.append(pname)
                    thirds_phone.append(p_phone)
                    thirds_id.append(p_id)
                else:
                    # 其他当事人追加身份后缀
                    others_name.append(f"{pname}({ptype})" if ptype else pname)
                    others_phone.append(p_phone)
                    others_id.append(p_id)

        # 构建主表的15列当事人数据 (使用 \n 回车换行拼接)
        party_columns_data = [
            "\n".join(clients_name), "\n".join(clients_phone), "\n".join(clients_id),
            "\n".join(plaintiffs_name), "\n".join(plaintiffs_phone), "\n".join(plaintiffs_id),
            "\n".join(defendants_name), "\n".join(defendants_phone), "\n".join(defendants_id),
            "\n".join(thirds_name), "\n".join(thirds_phone), "\n".join(thirds_id),
            "\n".join(others_name), "\n".join(others_phone), "\n".join(others_id)
        ]

        base_data_part1 = [
            case.case_id,
            case.case_number,
            format_date(case.commission_date),
            case.case_category
        ]

        base_data_part2 = [
            case.case_source or "",
            case.fee_method or "",
            case.risk_ratio or "",
            format_decimal(case.case_income),
            format_date(case.payment_due_date),
            case.cause or "",
            case.stage or "",
            case.agency_power or "",
            case.court or "",
            case.investigative_agency or "",
            case.procuratorate or "",
            case.second_instance_procuratorate or "",
            format_date(case.hearing_date),
            format_date(case.filing_date),
            format_date(case.closing_date),
            case.location or "",
            case.details or "",
            case.main_lawyer.real_name if case.main_lawyer else "",
            case.assistant_lawyer.real_name if case.assistant_lawyer else "",
            case.execution_lawyer.real_name if case.execution_lawyer else "",
            case.execution_assistant.real_name if case.execution_assistant else "",
            case.review_status,
            case.reviewer.real_name if case.reviewer else "",
            format_bool(case.is_major),
            format_bool(case.has_paper_file),
            format_bool(case.is_dismissed),
            format_bool(case.has_record),
            format_bool(case.has_preservation),
            format_date(case.preservation_start),
            format_date(case.preservation_end),
            case.case_code or "",
            case.closing_status or "",
            case.closing_method or "",
            format_date(case.litigation_fee_payment_date),
            format_decimal(case.litigation_fee_payment_amount),
            format_date(case.litigation_fee_refund_date),
            format_decimal(case.litigation_fee_refund_amount),
            format_date(case.execution_application_date),
            format_date(case.mediation_due_date),
            format_date(case.execution_due_date),
            format_date(case.advisory_due_date),
            format_datetime(case.created_at),
            format_datetime(case.updated_at)
        ]

        # 写入银行案件
        if case.case_category == "银行案件" and ws_bank:
            bank = case.bank_case_details
            bank_specific_data = [
                bank.branch_name if bank else "",
                bank.case_status if bank else "",
                bank.bank_required_case_status if bank else "",
                bank.missing_specific_materials if bank else "",
                bank.collateral_info if bank else "",
                bank.collateral_location if bank else "",
                bank.account_manager if bank else "",
                bank.loan_type if bank else "",
                bank.loan_account if bank else "",
                format_decimal(bank.loan_principal if bank else 0),
                format_decimal(bank.litigation_target_amount if bank else 0),
                format_decimal(bank.credit_card_penalty if bank else 0),
                format_date(bank.loan_date if bank else None),
                format_date(bank.loan_due_date if bank else None),
                format_date(bank.statute_of_limitations if bank else None),
                format_date(bank.case_acceptance_date if bank else None),
                bank.material_fetcher if bank else "",
                bank.pre_litigation_collection if bank else "",
                format_date(bank.seal_date if bank else None),
                format_date(bank.material_submission_date if bank else None),
                bank.handling_judge if bank else "",
                format_date(bank.judgment_date if bank else None),
                bank.judgment_method if bank else "",
                bank.judgment_summary if bank else "",
                format_decimal(bank.lawyer_fee_supported if bank else 0),
                format_decimal(bank.defendant_paid_lawyer_fee if bank else 0),
                format_bool(bank.is_settled if bank else False),
                format_bool(bank.has_second_instance_or_retrial if bank else False),
                bank.execution_case_number if bank else "",
                format_date(bank.execution_filing_date if bank else None),
                bank.execution_judge if bank else "",
                bank.borrower_work_unit if bank else "",
                format_bool(bank.is_execution_recovery if bank else False),
                format_date(bank.execution_material_receipt_date if bank else None),
                format_date(bank.execution_material_submission_date if bank else None),
                format_decimal(bank.execution_principal if bank else 0),
                format_decimal(bank.execution_lawyer_fee if bank else 0),
                bank.property_investigation if bank else "",
                bank.network_control_status if bank else "",
                bank.execution_plan if bank else "",
                bank.court_execution_measures if bank else "",
                format_date(bank.seizure_freeze_date if bank else None),
                bank.auction_status if bank else "",
                format_decimal(bank.auction_deal_price if bank else 0),
                bank.execution_settlement_content if bank else "",
                format_date(bank.procedure_termination_date if bank else None),
                bank.termination_reason if bank else "",
                format_date(bank.execution_conclusion_date if bank else None),
                format_date(bank.execution_recovery_date if bank else None),
                format_date(bank.payoff_date if bank else None),
                format_decimal(bank.execution_collection_amount if bank else 0),
                bank.collection_source if bank else "",
                format_json(bank.execution_settlement_log if bank else None),
                format_json(bank.deduction_log if bank else None),
                bank.mediation_tracking if bank else ""
            ]
            row_data = base_data_part1 + party_columns_data + base_data_part2 + bank_specific_data
            ws_bank.append(row_data)
            # 给15个当事人列（即第5到第19列）设置自动换行和居中对齐
            for col_idx in range(5, 20):
                ws_bank.cell(row=ws_bank.max_row, column=col_idx).alignment = Alignment(wrap_text=True,
                                                                                        vertical="center")

        # 写入常规案件
        elif case.case_category != "银行案件" and ws_standard:
            row_data = base_data_part1 + party_columns_data + base_data_part2
            ws_standard.append(row_data)
            # 给15个当事人列（即第5到第19列）设置自动换行和居中对齐
            for col_idx in range(5, 20):
                ws_standard.cell(row=ws_standard.max_row, column=col_idx).alignment = Alignment(wrap_text=True,
                                                                                                vertical="center")

    # ---------------- 自适应列宽逻辑 ----------------
    def auto_fit_columns(worksheet):
        for col in worksheet.columns:
            max_length = 0
            col_letter = col[0].column_letter

            for col_cell in col:
                if col_cell.value is not None:
                    # 将单元格内容转为字符串
                    cell_str = str(col_cell.value)

                    # 按换行符拆分，计算单行最长字符
                    # 这样可以兼容多个当事人通过 \n 换行的情况，同时保证最长公司名不断行
                    lines = cell_str.split('\n')
                    for line in lines:
                        # 中文按2个字符宽度算，英文/数字按1.2个字符宽度算
                        line_len = sum(2 if ord(c) > 255 else 1.2 for c in line)
                        if line_len > max_length:
                            max_length = line_len

            # 设置自适应宽度：加2作为缓冲空白，最高限制为100（防止极端异常数据导致列宽过大）
            adjusted_width = min(max_length + 2, 100)
            worksheet.column_dimensions[col_letter].width = adjusted_width

    # 对存在的Sheet应用列宽自适应
    if ws_standard:
        auto_fit_columns(ws_standard)
    if ws_bank:
        auto_fit_columns(ws_bank)
    if ws_parties:
        auto_fit_columns(ws_parties)

    # 5. 保存到内存并返回
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer