# database/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from ..core.config import DATABASE_URL


# 创建数据库引擎，pool_pre_ping=True表示在使用连接前先ping一下数据库确认连接有效性
engine = create_engine(DATABASE_URL, pool_pre_ping= True,echo=True)
# 创建数据库会话工厂，autocommit=False表示不自动提交事务，autoflush=False表示不自动刷新，bind绑定到指定的数据库引擎
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# 创建 declarative_base 类，用于定义数据库模型基类
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
