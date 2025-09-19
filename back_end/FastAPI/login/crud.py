# crud.py
from sqlalchemy.orm import Session
from .models import User

def get_user_by_account(db: Session, account: str):
    """
    根据账号查询用户
    """
    return db.query(User).filter(User.accounts == account).first()

