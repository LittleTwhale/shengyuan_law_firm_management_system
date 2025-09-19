# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from passlib.hash import bcrypt

from login.crud import get_user_by_account
from login.database import get_db
from login.schemas import LoginResponse, LoginRequest

app = FastAPI()

# 允许前端跨域 | Allow frontend cross-origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175"],  # Vue 开发端口（Vite 默认是 5173）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录接口
    User login API
    """
    user = get_user_by_account(db, request.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="账号不存在")

    # 验证密码哈希 | Verify password hash
    if not bcrypt.verify(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="密码错误 ")

    return {
        "message": "登录成功",
            "user": {
            "id": user.id,
            "role": user.role.value     # 律师/管理员
            }
        }