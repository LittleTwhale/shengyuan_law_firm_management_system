# core/config.py
import os
from dotenv import load_dotenv

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