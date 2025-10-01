# crud/case.py
from datetime import datetime

from sqlalchemy.orm import Session, joinedload
from ..models.case import Case
from typing import List, Optional, cast


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
        .filter(Case.case_id == case_id)
        .first()
    )


def list_cases_by_user_role(db: Session, user_id: int, role: str, skip: int = 0, limit: int = 100) -> List[Case]:
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
    )

    if role not in ["admin", "owner"]:
        query = query.filter(Case.main_lawyer_id == user_id)

    cases = query.offset(skip).limit(limit).all()
    return cast(list[Case],cases)

def count_cases_by_user_role(db: Session, user_id: int, role: str) -> int:
    """
    根据用户角色统计案件总数
    """
    query = db.query(Case)
    if role not in ["admin", "owner"]:
        query = query.filter(Case.main_lawyer_id == user_id)

    return query.count()


def create_case(db: Session, case_data: dict) -> Case:
    """
    创建新案件（系统自动生成案件号）
    """
    # 1. 获取年份
    year = datetime.now().year

    # 2. 案件类型映射
    type_map = {
        "民事案件": "民字",
        "刑事案件": "刑字",
        "仲裁案件": "仲字",
        "行政案件": "行字",
        "非诉案件": "非诉字",
        "法律顾问业务": "法顾字",
    }
    case_type = case_data.get("case_category")
    if case_type not in type_map:
        raise ValueError("未知的案件类型")

    # 3. 查询该类型的最新案件号
    latest_case = db.query(Case).filter(
        Case.case_category == case_type,
        Case.case_number.like(f"湘生律（{year}）%")
    ).order_by(Case.case_id.desc()).first()

    # 4. 生成下一个序号
    if latest_case:
        last_number = int(latest_case.case_number.split("第")[-1].replace("号", ""))
        next_number = last_number + 1
    else:
        next_number = 1

    # 5. 拼接案件号
    case_number = f"湘生律（{year}）{type_map[case_type]}第{next_number}号"

    # 6. 创建案件
    new_case = Case(**case_data, case_number=case_number)
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    return new_case


def update_case(db: Session, case_id: int, update_data: dict) -> Optional[Case]:
    """
    更新已有案件
    """
    case = cast(
        Optional[Case],
        db.query(Case)
        .options(
            joinedload(Case.main_lawyer),
            joinedload(Case.assistant_lawyer),
            joinedload(Case.execution_lawyer),
            joinedload(Case.execution_assistant),
        )
        .filter(Case.case_id == case_id)
        .first(),
    )
    if not case:
        return None

    for key, value in update_data.items():
        if hasattr(case, key):
            setattr(case, key, value)

    db.commit()
    db.refresh(case)
    return case


def delete_case(db: Session, case_id: int) -> bool:
    """
    删除案件
    """
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        return False

    db.delete(case)
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
            (Case.main_lawyer_id == lawyer_id)
            | (Case.assistant_lawyer_id == lawyer_id)
            | (Case.execution_lawyer_id == lawyer_id)
            | (Case.execution_assistant_id == lawyer_id)
        )
        .all(),
    )
