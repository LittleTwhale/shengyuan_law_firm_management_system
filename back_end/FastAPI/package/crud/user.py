# crud/user.py
from sqlalchemy.orm import Session
from ..core.security import verify_password,hash_password
from ..models.user import User
from ..schemas.user import UserCreate
from typing import Optional, List, cast


def get_user_by_accounts(db: Session, accounts: str) -> Optional[User]:
    """
    根据账号查询用户
    """
    return db.query(User).filter(User.accounts == accounts).first()


def authenticate_user(db: Session, accounts: str, password: str) -> Optional[User]:
    """
    用户登录验证
    """
    user = get_user_by_accounts(db, accounts)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def create_user(db: Session, user_in: UserCreate) -> User:
    """
    创建新用户
    """
    hashed_password = hash_password(user_in.password)
    db_user = User(
        accounts=user_in.accounts,
        password_hash=hashed_password,
        real_name=user_in.real_name,
        role=user_in.role,
        position=user_in.position
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, update_data: dict) -> Optional[User]:
    """
    修改用户信息
    """
    user : Optional[User] = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    for key, value in update_data.items():
        if key == "password":  # 如果修改密码
            value = hash_password(value)
            setattr(user, "password_hash", value)
        elif hasattr(user, key):
            setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user

def get_users(db: Session) -> List[User]:
    """
    获取用户列表
    """
    users = db.query(User).all()
    return cast(List[User], users)

def get_ordinary_users(db: Session) -> List[User]:
    """
    获取普通用户列表
    """
    users = db.query(User).filter(User.role == "user").all()
    return cast(List[User], users)