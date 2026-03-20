import logging
import sys
import os
import datetime
from .config import LOG_ROOT


# =============================================================================
# 1. 自定义 Handler：实现按日期生成目录
# =============================================================================
class DailyPathFileHandler(logging.FileHandler):
    def __init__(self, base_dir, mode='a', encoding='utf-8', delay=False):
        self.base_dir = base_dir
        self.current_date = datetime.date.today()
        # 初始化时，先计算出当天的文件路径
        filename = self._build_filename(self.current_date)
        # 调用父类初始化
        super().__init__(filename, mode, encoding, delay)

    def _build_filename(self, date_obj):
        """
        根据日期构建路径：base_dir/年份/月份/日期.log
        """
        year_str = date_obj.strftime("%Y")
        month_str = date_obj.strftime("%m")
        day_str = date_obj.strftime("%d")

        # 拼接目录路径：logs/2023/10
        dir_path = os.path.join(self.base_dir, year_str, month_str)

        # 如果目录不存在，则创建
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        # 返回完整文件路径
        return os.path.join(dir_path, f"{day_str}.log")

    def emit(self, record):
        """
        每次写入日志时触发，检查是否跨天
        """
        new_date = datetime.date.today()

        # 如果当前日期与记录日期不一致，说明跨天了
        if new_date != self.current_date:
            self.current_date = new_date

            # 1. 关闭旧文件流
            self.close()

            # 2. 更新文件名属性
            self.baseFilename = self._build_filename(self.current_date)

            # 3. 重置流对象为空，下次 emit 时父类会自动用新文件名打开
            self.stream = None

        # 调用父类的写入逻辑
        super().emit(record)


# =============================================================================
# 2. 定义格式器
# =============================================================================

# 文件中的日志格式（清晰文本，无颜色）
FILE_FORMATTER = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# 控制台的日志格式（用于我们自己的业务代码）
# 注意：Uvicorn 自己的控制台格式不需要在这里定义，它会使用自带的彩色格式
CONSOLE_FORMATTER = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


# =============================================================================
# 3. 初始化日志配置函数
# =============================================================================
def setup_logging():
    # 确保日志根目录存在
    if not os.path.exists(LOG_ROOT):
        os.makedirs(LOG_ROOT, exist_ok=True)

    # 创建文件处理器 (用于写入 logs/202x/xx/xx.log)
    file_handler = DailyPathFileHandler(base_dir=LOG_ROOT, encoding="utf-8")
    file_handler.setFormatter(FILE_FORMATTER)

    # ---------------------------------------------------------------
    # 配置 Uvicorn 的日志 (关键点：保留原有的彩色输出)
    # ---------------------------------------------------------------
    # 遍历 uvicorn 的相关 logger，将我们的 file_handler "追加" 进去
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        # 获取 uvicorn 已经建立好的 logger
        uvicorn_logger = logging.getLogger(logger_name)

        # 仅仅添加文件处理器，不要去覆盖 uvicorn_logger.handlers 列表
        # 避免重复添加：先检查一下是否已经有了我们的 file_handler
        # (防止 reload 时重复添加导致日志双倍写入)
        if not any(isinstance(h, DailyPathFileHandler) for h in uvicorn_logger.handlers):
            uvicorn_logger.addHandler(file_handler)

    # ---------------------------------------------------------------
    # 配置 SQLAlchemy 日志 (核心修改：关闭普通 SQL 输出，解除多线程 I/O 阻塞)
    # ---------------------------------------------------------------
    db_logger = logging.getLogger("sqlalchemy.engine")

    # 1. 改为 WARNING，只有报错或警告时才记录，彻底关闭海量的常规 SQL 打印
    db_logger.setLevel(logging.WARNING)

    if not any(isinstance(h, DailyPathFileHandler) for h in db_logger.handlers):
        db_logger.addHandler(file_handler)

    # 2. 务必取消注释：彻底阻止日志向上层（控制台）冒泡
    db_logger.propagate = False

    # ---------------------------------------------------------------
    # 配置应用自己的 Logger (shengyuan_app)
    # ---------------------------------------------------------------
    app_logger = logging.getLogger("shengyuan_app")
    app_logger.setLevel(logging.INFO)

    # 如果 app_logger 还没有 handler，则添加
    if not app_logger.handlers:
        # 1. 添加控制台输出 (StreamHandler)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(CONSOLE_FORMATTER)
        app_logger.addHandler(console_handler)

        # 2. 添加文件输出 (DailyPathFileHandler)
        app_logger.addHandler(file_handler)

    # 防止日志向上层重复冒泡
    app_logger.propagate = False

    return app_logger


# =============================================================================
# 4. 执行初始化并导出 logger
# =============================================================================
logger = setup_logging()