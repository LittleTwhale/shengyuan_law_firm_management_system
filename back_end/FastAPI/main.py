# main.py
import time
from fastapi import FastAPI, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .package.api.login import router as auth_login_router
from .package.api.lawyer_manage import router as auth_lawyer_router
from .package.api.case_manage import router as auth_case_router
from .package.api.case_review import router as auth_case_review_router
from .package.api.user_profile import router as auth_user_router
from .package.api.attachment import router as auth_attachment_router
from .package.api.template import router as auth_template_router
from .package.api.electronic_seal import router as auth_seal_router
from .package.api.admin import router as auth_admin_router
from .package.api.finance_api import router as auth_finance_router
from .package.api.party_building_api import router as auth_party_building_router
from .package.api.electronic_volume_api import router as auth_electronic_volume_router
from .package.core.config import PARTY_IMAGE_ROOT
from .package.core.logger import logger

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://119.45.129.216:8080",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]


#  定义 lifespan 上下文管理器（包含 startup 逻辑）
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行的代码
    logger.info("==================================================")
    logger.info("日志系统已加载，当前日志模式：每日独立存储及自动清理")
    logger.info("系统全局 API 前缀已启用: /api")
    logger.info("==================================================")

    yield  # 用于分隔启动和关闭逻辑


# 初始化 FastAPI 实例
app = FastAPI(lifespan=lifespan)

# =================================================================
# 1. 注册 CORS 中间件
# =================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =================================================================
# 2. 注册高级日志拦截器 Middleware
# =================================================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # 获取客户端 IP (优先读取 Nginx 转发的 X-Forwarded-For)
    client_ip = request.headers.get("X-Forwarded-For") or request.client.host

    # 执行后续的业务逻辑
    response = await call_next(request)

    # 计算耗时 (毫秒)
    process_time = (time.time() - start_time) * 1000

    # 构建结构化的高价值日志
    log_msg = (
        f"<== 响应: [{request.method}] {request.url.path} | "
        f"状态码: {response.status_code} | "
        f"IP: {client_ip} | "
        f"耗时: {process_time:.2f} ms"
    )

    # 根据状态码使用不同的日志级别
    if response.status_code >= 500:
        logger.error(log_msg)
    elif response.status_code >= 400:
        logger.warning(log_msg)
    else:
        logger.info(log_msg)

    return response


# =================================================================
# 3. 静态文件挂载 (不受 /api 前缀影响)
# =================================================================
# 静态文件挂载
app.mount("/templates", StaticFiles(directory="FastAPI/static/template"), name="templates")
# 挂载党建图片目录
app.mount("/static_resources/party_images", StaticFiles(directory=PARTY_IMAGE_ROOT), name="party_images")

# =================================================================
# 4. 注册带 /api 前缀的业务路由
# =================================================================
# 创建一个统一带有 /api 前缀的路由组
api_router = APIRouter(prefix="/api")

# 将所有的业务路由注册到这个 api_router 下

# 注册登录路由
api_router.include_router(auth_login_router)

# 注册人员管理路由
api_router.include_router(auth_lawyer_router)

# 注册业务管理路由
api_router.include_router(auth_case_router)

# 注册业务审核路由
api_router.include_router(auth_case_review_router)

# 注册用户管理路由
api_router.include_router(auth_user_router)

# 注册附件管理路由
api_router.include_router(auth_attachment_router)

# 注册模板路由
api_router.include_router(auth_template_router)

# 注册电子印章路由
api_router.include_router(auth_seal_router)

# 注册权限管理路由
api_router.include_router(auth_admin_router)

# 注册财务管理路由
api_router.include_router(auth_finance_router)

# 注册党建管理路由
api_router.include_router(auth_party_building_router)

# 注册电子卷宗管理路由
api_router.include_router(auth_electronic_volume_router)

# 最后将这个路由组挂载到 app 实例上
app.include_router(api_router)