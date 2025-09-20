# crud/user.py
from sqlalchemy.orm import Session
from ..core.security import verify_password
from ..models.user import User
from typing import Optional


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
