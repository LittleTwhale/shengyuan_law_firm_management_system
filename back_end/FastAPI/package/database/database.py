# database/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from ..core.config import DATABASE_URL

# 创建数据库引擎，扩容连接池，并优化了多线程下的配置
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,         # 建议在批量并发场景下关闭，避免控制台 I/O 阻塞拖慢速度。如需调试可暂时改回 True
    pool_size=20,       # 基础连接数（建议略大于线程池的 max_workers，比如 15 个线程配 20 个连接）
    max_overflow=30,    # 超过基础连接数时，最多还能额外创建的连接数（总并发可达 50）
    pool_timeout=30,    # 拿不到连接时的最长等待时间（秒）
    pool_recycle=1800   # 半小时回收一次连接，防止数据库端主动断开闲置连接
)

# 创建数据库会话工厂，autocommit=False表示不自动提交事务，autoflush=False表示不自动刷新，bind绑定到指定的数据库引擎
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# 创建 declarative_base 类，用于定义数据库模型基类
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        # 这里处理业务逻辑中的异常
        raise
    finally:
        try:
            db.close()
        except (AttributeError, TypeError):
            # 捕获由于关闭过程导致的 NoneType 报错
            pass