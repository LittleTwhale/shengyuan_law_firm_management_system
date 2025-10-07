# crud/case.py
from datetime import datetime
from typing import List, Optional, cast

from sqlalchemy.orm import Session, joinedload

from ..models.case import Case
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
    keyword: Optional[str] = None,  # 新增
    category: Optional[str] = None  # 新增
) -> List[Case]:
    """
    根据用户角色返回案件列表
    - 普通用户：只能看到自己为主办律师的案件
    - admin/owner：可以看到全部案件
    """
    query = db.query(Case).options(
        joinedload(Case.main_lawyer),
        joinedload(Case.assistant_lawyer),
        joinedload(Case.execution_lawyer),
        joinedload(Case.execution_assistant),
    ).filter(Case.is_deleted == False)

    # 角色筛选
    if role not in ["admin", "owner"]:
        query = query.filter(Case.main_lawyer_id == user_id)

    # 类别筛选
    if category:
        query = query.filter(Case.case_category == category)

    # 关键词搜索（案件号或委托人）
    if keyword:
        query = query.filter(
            (Case.case_number.like(f"%{keyword}%")) |
            (Case.client_name.like(f"%{keyword}%"))
        )

    cases = query.offset(skip).limit(limit).all()
    return cast(list[Case], cases)

def count_cases_by_user_role(
    db: Session,
    user_id: int,
    role: str,
    keyword: Optional[str] = None,  # 新增
    category: Optional[str] = None  # 新增
) -> int:
    """
    根据用户角色统计案件总数
    """
    query = db.query(Case).filter(Case.is_deleted == False)
    # 角色筛选
    if role not in ["admin", "owner"]:
        query = query.filter(Case.main_lawyer_id == user_id)

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
) -> List[Case]:
    """
    根据用户角色返回银行案件列表
    - 普通用户：只能看到自己为主办律师的案件
    - admin/owner：可以看到全部案件
    """
    query = db.query(Case).options(
        joinedload(Case.main_lawyer),
        joinedload(Case.assistant_lawyer),
        joinedload(Case.execution_lawyer),
        joinedload(Case.execution_assistant),
    ).filter(Case.is_deleted == False,Case.is_bank_case == True)

    # 角色筛选
    if role not in ["admin", "owner"]:
        query = query.filter(Case.main_lawyer_id == user_id)

    # 关键词搜索（案件号或委托人）
    if keyword:
        query = query.filter(
            (Case.case_number.like(f"%{keyword}%")) |
            (Case.client_name.like(f"%{keyword}%"))
        )

    cases = query.offset(skip).limit(limit).all()
    return cast(list[Case], cases)

def count_bank_cases_by_user_role(
    db: Session,
    user_id: int,
    role: str,
    keyword: Optional[str] = None,  # 新增
) -> int:
    """
    根据用户角色统计案件总数
    """
    query = db.query(Case).filter(Case.is_deleted == False,Case.is_bank_case == True)
    # 角色筛选
    if role not in ["admin", "owner"]:
        query = query.filter(Case.main_lawyer_id == user_id)

    # 关键词搜索
    if keyword:
        query = query.filter(
            (Case.case_number.like(f"%{keyword}%")) |
            (Case.client_name.like(f"%{keyword}%"))
        )

    return query.count()


def create_case(db: Session, case_in: CaseCreate) -> Case:
    """
    创建新案件（系统自动生成案件号）
    """
    year = datetime.now().year

    # 案件类型映射
    type_map = {
        "民事案件": "民字",
        "刑事案件": "刑字",
        "仲裁案件": "仲字",
        "行政案件": "行字",
        "非诉案件": "非诉字",
        "法律顾问业务": "法顾字",
    }

    case_type = case_in.case_category
    if case_type not in type_map:
        raise ValueError("未知的案件类型")

    # 查询该类型的最新案件号
    latest_case = db.query(Case).filter(
        Case.case_category == case_type,
        Case.case_number.like(f"湘生律（{year}）%")
    ).order_by(Case.case_id.desc()).first()

    next_number = 1
    if latest_case:
        last_number = int(latest_case.case_number.split("第")[-1].replace("号", ""))
        next_number = last_number + 1

    case_number = f"湘生律（{year}）{type_map[case_type]}第{next_number}号"

    # 将输入数据转换为字典
    case_data = case_in.model_dump()

    # 强制设置默认值
    case_data["review_status"] = "待审核"
    case_data["is_deleted"] = False

    # 创建案件实例
    new_case = Case(**case_data, case_number=case_number)
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    return new_case


def update_case(db: Session, case_id: int, case_in: CaseUpdate) -> Optional[Case]:
    """
    更新已有案件
    """
    case = db.query(Case).options(
        joinedload(Case.main_lawyer),
        joinedload(Case.assistant_lawyer),
        joinedload(Case.execution_lawyer),
        joinedload(Case.execution_assistant),
    ).filter(
        Case.case_id == case_id,
        Case.is_deleted == False
    ).first()

    if not case:
        return None

    for key, value in case_in.model_dump(exclude_unset=True).items():
        setattr(case, key, value)
    case.review_status = "待审核"

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

    case.is_deleted = True
    db.commit()
    return True


def list_cases_by_lawyer(db: Session, lawyer_id: int) -> List[Case]:
    """
    获取指定律师相关的案件（主办/助理/执行律师/执行助理）
    """
    return cast(
        List[Case],
        db.query(Case)
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
        .all(),
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
        query = query.filter(Case.main_lawyer_id == user_id,Case.is_deleted == False)

    return cast(list[Case], query.all())