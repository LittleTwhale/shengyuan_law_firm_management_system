# main.py
import time
from fastapi import FastAPI, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
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
from .package.api.system_announcement_api import router as auth_system_announcement_router
from .package.api.system_admin import router as auth_system_admin_router
from .package.api.monitor import router as auth_monitor_router
from .package.api.ai_assistant_api import router as auth_ai_router
from .package.api.legal_kb_api import router as auth_legal_kb_router
from .package.api.error_analysis_api import router as auth_error_analysis_router
from .package.core.config import PARTY_IMAGE_ROOT, SECRET_KEY, ALGORITHM
from .package.core.logger import logger
from .package.core.user_cache import user_cache
from .package.utils.search_engine import init_meilisearch
from .package.utils.request_tracker import request_tracker
from .package.utils.error_analyzer import prepare_error_analysis, run_analysis
import asyncio
from jose import jwt as jose_jwt

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
    logger.info("用户缓存系统已启用，缓存TTL: 5分钟")
    logger.info("系统全局 API 前缀已启用: /api")
    logger.info("错误分析系统已加载，未捕获异常将触发 DeepSeek 自动分析")
    logger.info("==================================================")
    # 初始化 Meilisearch
    try:
        init_meilisearch()
        logger.info("Meilisearch 搜索引擎索引初始化成功")
    except Exception as e:
        logger.error(f"Meilisearch 搜索引擎初始化失败，请检查服务是否启动: {e}")

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
    expose_headers=["Content-Disposition"]
)


# =================================================================
# 2. 注册高级日志拦截器 Middleware
# =================================================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # 获取客户端 IP (优先读取 Nginx 转发的 X-Forwarded-For)
    client_ip = request.headers.get("X-Forwarded-For") or request.client.host

    # 获取用户信息
    username = "匿名用户"
    user_accounts = None
    try:
        # 尝试从请求头获取 Authorization token
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            # 使用缓存获取用户信息
            username = user_cache.get_user_display_name(token)
            # 解码 token 获取 accounts 用于活跃用户追踪
            try:
                payload = jose_jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_accounts = payload.get("sub")
            except Exception:
                pass
    except Exception:
        # 获取用户信息失败，保持默认用户名
        pass

    # 在 request.state 中保存用户上下文，供全局异常处理器使用
    request.state.username = username
    request.state.user_accounts = user_accounts

    # 记录请求用于 QPS 和活跃用户统计
    request_tracker.record_request(user_accounts)

    # 执行后续的业务逻辑
    response = await call_next(request)

    # 计算耗时 (毫秒)
    process_time = (time.time() - start_time) * 1000

    # 构建结构化的高价值日志
    log_msg = (
        f"<== 响应: [{request.method}] {request.url.path} | "
        f"状态码: {response.status_code} | "
        f"用户: {username} | "
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
# 2.5 全局异常处理器 — 捕获未处理异常，触发 DeepSeek 后台分析
# =================================================================


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器（两阶段）：
    1. 同步：提取错误信息 → 去重 → 创建 DB 记录 → 拿到 analysis_id
    2. 异步：后台调用 DeepSeek 分析 → 更新 DB 结果
    3. 返回：500 响应中立即带回 analysis_id，供前端轮询弹窗

    防御性设计：外层 try/except 确保即使 prepare_error_analysis 抛出
    未预期的异常，也能返回合法的 JSON 响应（含 CORS 头），避免前端
    因浏览器拦截而出现 Network Error。
    """
    # 记录错误日志
    try:
        logger.error(
            "未捕获异常: %s %s | %s: %s",
            request.method,
            request.url.path,
            type(exc).__name__,
            str(exc),
            exc_info=True,
        )
    except Exception:
        pass  # 日志记录失败不应影响错误响应

    # 提取 origin 用于手动 CORS 头（防止 CORS 中间件对 500 响应失效）
    origin = request.headers.get("origin", "*")

    try:
        # 阶段一：同步创建分析记录（拿到 analysis_id）
        analysis_info = prepare_error_analysis(exc, request)

        analysis_id = analysis_info.get("analysis_id")
        is_duplicate = analysis_info.get("is_duplicate", False)

        # 构建响应内容
        if is_duplicate and analysis_id is not None:
            response_content = {
                "detail": "此错误刚刚已分析过，以下是分析建议",
                "analysis_id": analysis_id,
                "analysis_status": "completed",
                "analysis_result": analysis_info.get("result"),
                "error_type": analysis_info.get("error_type"),
            }
        elif analysis_id is not None:
            asyncio.create_task(run_analysis(analysis_id))
            response_content = {
                "detail": "系统正在分析此错误，分析完成后将自动弹出结果",
                "analysis_id": analysis_id,
                "analysis_status": "pending",
            }
        else:
            response_content = {
                "detail": "服务器内部错误，请稍后重试",
            }
    except Exception as handler_err:
        # 异常处理器自身出错时的最终兜底
        logger.error("全局异常处理器自身异常: %s", handler_err, exc_info=True)
        response_content = {
            "detail": "服务器内部错误，请稍后重试",
        }

    # 手动添加 CORS 头，确保浏览器不会拦截 500 响应
    return JSONResponse(
        status_code=500,
        content=response_content,
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )


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

# 注册系统公告管理路由
api_router.include_router(auth_system_announcement_router)

# 注册系统管理路由
api_router.include_router(auth_system_admin_router)

# 注册服务器资源监控路由
api_router.include_router(auth_monitor_router)

# 注册案件智能分析路由
api_router.include_router(auth_ai_router)

# 注册法律知识库路由
api_router.include_router(auth_legal_kb_router)

# 注册错误分析路由
api_router.include_router(auth_error_analysis_router)



# 最后将这个路由组挂载到 app 实例上
app.include_router(api_router)