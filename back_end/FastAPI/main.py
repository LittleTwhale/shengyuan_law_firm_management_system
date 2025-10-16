# main.py
from fastapi import FastAPI
from .package.api.login import router as auth_login_router
from .package.api.lawyer_manage import router as auth_lawyer_router
from .package.api.case_manage import router as auth_case_router
from .package.api.case_review import router as auth_case_review_router
from .package.api.user_profile import router as auth_user_router
from .package.api.attachment import router as auth_attachment_router
from .package.api.template import router as auth_template_router

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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

# 静态文件挂载
app.mount("/templates", StaticFiles(directory="FastAPI/static/template"), name="templates")

# 注册登录路由
app.include_router(auth_login_router)

# 注册律师管理路由
app.include_router(auth_lawyer_router)

# 注册案件管理路由
app.include_router(auth_case_router)

# 注册案件附件路由
app.include_router(auth_attachment_router)

# 注册案件审核路由
app.include_router(auth_case_review_router)

# 注册用户信息路由
app.include_router(auth_user_router)

# 注册模板路由
app.include_router(auth_template_router)