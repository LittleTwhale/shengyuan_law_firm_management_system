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
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # token过期时间（分钟）

# 附件根目录
CASE_ATTACHMENT_ROOT = os.path.join("D:\\", "syls", "database", "attachments")  # 自动处理路径分隔符（兼容Windows/Linux）

# 文书模板根目录
DOCUMENT_TEMPLATE_ROOT = os.path.join("D:\\", "syls", "database", "templates")

# 印章存储根目录
ELECTRONIC_SEAL_ROOT = os.path.join("D:\\", "syls", "database", "seals")

# 用印申请文件存储根目录
SEAL_APPLICATION_ROOT = os.path.join("D:\\", "syls", "database", "seal_applications")