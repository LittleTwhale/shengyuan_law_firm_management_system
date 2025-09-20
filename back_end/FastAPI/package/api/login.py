# api/login.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..schemas.user import UserLogin, Token
from ..crud.user import authenticate_user
from ..core.security import create_access_token
from datetime import timedelta

# 创建一个路由对象
router = APIRouter(
    prefix="/auth",   # 路径前缀 => /auth/login
    tags=["auth"]     # 接口标签 => "认证相关"
)

# 登录接口
@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录接口
    - 接收账号和密码
    - 验证成功后返回 JWT token
    """
    user = authenticate_user(db, user_data.accounts, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 设置 token 过期时间，例如 1 小时
    access_token_expires = timedelta(minutes=60)

    # 生成 JWT token
    access_token = create_access_token(
        data={"sub": user.accounts, "role": user.role},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "accounts": user.accounts,
            "real_name": user.real_name,
            "role": user.role,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
    }
