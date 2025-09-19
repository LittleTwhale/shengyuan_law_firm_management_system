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
SECRET_KEY = os.getenv("SECRET_KEY", "changeme123")  # JWT秘钥
ALGORITHM = "HS256"  # 加密算法
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # token过期时间（分钟）