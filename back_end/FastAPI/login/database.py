# database.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 加载环境变量
load_dotenv()
# 从环境变量中读取密码
db_password = os.getenv("DB_PASSWORD")

# 数据库连接URL，使用MySQL数据库，
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://newuser:{db_password}@127.0.0.1:3306/shengyuan_db"

# 创建数据库引擎，pool_pre_ping=True表示在使用连接前先ping一下数据库确认连接有效性
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
# 创建数据库会话工厂，autocommit=False表示不自动提交事务，autoflush=False表示不自动刷新，bind绑定到指定的数据库引擎
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建 declarative_base 类，用于定义数据库模型基类
Base = declarative_base()

def get_db():
    """
    获取数据库会话的生成器函数

    该函数创建一个新的数据库会话并将其返回给调用者。
    使用try-finally确保即使发生异常也会正确关闭数据库连接。

    Yields:
        Session: 数据库会话对象

    注意:
        使用完毕后会自动关闭数据库连接
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
