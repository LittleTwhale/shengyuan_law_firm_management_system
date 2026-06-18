# core/config.py
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# 加载环境变量
load_dotenv()

# 从环境变量中读取密码
db_password = os.getenv("DB_PASSWORD")

# 数据库连接URL，使用MySQL数据库
DATABASE_URL = f"mysql+pymysql://newuser:{db_password}@localhost:3306/shengyuan_db"


# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY")  # JWT秘钥
ALGORITHM = "HS256"  # 加密算法
ACCESS_TOKEN_EXPIRE_MINUTES = 300  # token过期时间（分钟）

# DeepSeek API 配置（案件智能分析）
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")  # DeepSeek API 密钥
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")  # API 地址

# Meilisearch 搜索引擎配置
MEILI_URL = os.getenv("MEILI_URL", "http://localhost:7700")
MEILI_MASTER_KEY = os.getenv("MEILI_MASTER_KEY")

# 附件根目录
CASE_ATTACHMENT_ROOT = os.path.join("D:\\", "syls", "database", "attachments")  # 自动处理路径分隔符（兼容Windows/Linux）

# 文书模板根目录
DOCUMENT_TEMPLATE_ROOT = os.path.join("D:\\", "syls", "database", "templates")

# 印章存储根目录
ELECTRONIC_SEAL_ROOT = os.path.join("D:\\", "syls", "database", "seals")

# 用印申请文件存储根目录
SEAL_APPLICATION_ROOT = os.path.join("D:\\", "syls", "database", "seal_applications")

# 模板路径
TEMPLATE_DIR = os.path.join("FastAPI", "static", "template")

# 日志存储根目录
LOG_ROOT = os.path.join("D:\\", "syls", "database", "logs")

# 党建附件存储路径
PARTY_FILE_ROOT = os.path.join("D:\\", "syls", "database", "party_building_attachments")

# 党建富文本图片存储路径
PARTY_IMAGE_ROOT = os.path.join("D:\\", "syls", "database", "party_building_rich_text_images")

# 电子卷宗文件存储路径
ELECTRONIC_VOLUME_ROOT = os.path.join("D:\\", "syls", "database", "electronic_volumes")

# 合并后的电子卷宗 PDF 存储路径
PDF_VOLUME_ROOT = os.path.join("D:\\", "syls", "database", "pdf_volumes")


class Settings(BaseSettings):
    """存储配置 — 支持本地文件系统与腾讯云 COS 切换"""

    # 存储类型: "LOCAL"（本地文件系统）或 "COS"（腾讯云对象存储）
    STORAGE_TYPE: str = "LOCAL"

    # 腾讯云 COS 配置（STORAGE_TYPE == "COS" 时需设置）
    COS_SECRET_ID: str = ""
    COS_SECRET_KEY: str = ""
    COS_BUCKET: str = ""
    COS_REGION: str = ""
    COS_STS_ROLE_ARN: str = ""  # 用于签发前端直传临时密钥的角色 ARN

    model_config = {"env_file": ".env", "extra": "ignore"}


# 全局配置实例（导入时自动从环境变量或 .env 文件加载）
settings = Settings()


def get_volume_storage_prefix(case_id, volume_id):
    """
    获取卷宗文件存储的相对目录前缀
    - 绑定案件：case_{case_id}/vol_{volume_id}
    - 独立卷宗：standalone/vol_{volume_id}
    """
    prefix = f"case_{case_id}" if case_id else "standalone"
    return os.path.join(prefix, f"vol_{volume_id}")