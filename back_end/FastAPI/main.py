# main.py
from fastapi import FastAPI
from .package.api.login import router as auth_login_router
from .package.api.lawyer_manage import router as auth_lawyer_router
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]


# 注册路由
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册登录路由
app.include_router(auth_login_router)

# 注册律师管理路由
app.include_router(auth_lawyer_router)