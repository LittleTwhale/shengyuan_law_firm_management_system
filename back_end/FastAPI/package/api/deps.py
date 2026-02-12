# api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from pydantic import ValidationError

from ..database.database import get_db
from ..core.config import SECRET_KEY, ALGORITHM
from ..models.user import User
from ..crud import user as crud_user

# 这里的 tokenUrl 应该对应你 api/login.py 里的路由地址
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
        db: Session = Depends(get_db),
        token: str = Depends(oauth2_scheme)
) -> User:
    """
    核心依赖：验证 Token 并获取当前用户对象
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 1. 解码 Token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # 2. 获取 sub 字段 (根据你的 login.py，这里存的是 accounts 字符串)
        user_accounts: str = payload.get("sub")

        if user_accounts is None:
            raise credentials_exception

    except (JWTError, ValidationError):
        raise credentials_exception

    # 3. 根据账号 (accounts) 从数据库查找用户
    # 你的 crud/user.py 中已经有这个函数了
    user = crud_user.get_user_by_accounts(db, accounts=user_accounts)

    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(
        current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前活跃用户 (可在后续扩展 banned 状态检查)
    """
    return current_user