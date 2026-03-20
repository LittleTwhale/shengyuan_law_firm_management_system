import logging
import sys
import os
import datetime
import shutil
from .config import LOG_ROOT


# =============================================================================
# 自定义 Handler：实现按日期生成目录 & 自动清理过期日志
# =============================================================================
class DailyPathFileHandler(logging.FileHandler):
    def __init__(self, base_dir, mode='a', encoding='utf-8', delay=False, retention_days=30):
        self.base_dir = base_dir
        self.retention_days = retention_days
        self.current_date = datetime.date.today()

        # 初始化时触发一次清理
        self._clean_old_logs()

        filename = self._build_filename(self.current_date)
        super().__init__(filename, mode, encoding, delay)

    def _build_filename(self, date_obj):
        year_str = date_obj.strftime("%Y")
        month_str = date_obj.strftime("%m")
        day_str = date_obj.strftime("%d")
        dir_path = os.path.join(self.base_dir, year_str, month_str)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        return os.path.join(dir_path, f"{day_str}.log")

    def emit(self, record):
        # 每天跨天时，自动切换日志文件，并清理旧日志
        new_date = datetime.date.today()
        if self.current_date != new_date:
            self.current_date = new_date
            self.close()
            self.baseFilename = self._build_filename(self.current_date)
            self.stream = self._open()
            # 跨天时触发清理过期日志
            self._clean_old_logs()
        super().emit(record)

    def _clean_old_logs(self):
        """自动清理超过保留天数的日志文件及空目录"""
        if not os.path.exists(self.base_dir):
            return

        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.retention_days)

        # 1. 删除过期的 .log 文件
        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith(".log"):
                    file_path = os.path.join(root, file)
                    # 获取文件最后修改时间
                    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                    if mtime < cutoff_date:
                        try:
                            os.remove(file_path)
                        except Exception:
                            pass

        # 2. 清理空文件夹 (自下而上清理)
        for root, dirs, files in os.walk(self.base_dir, topdown=False):
            for d in dirs:
                dir_path = os.path.join(root, d)
                if not os.listdir(dir_path):  # 如果文件夹为空
                    try:
                        os.rmdir(dir_path)
                    except Exception:
                        pass


# =============================================================================
# 全局日志配置
# =============================================================================
class ColorFormatter(logging.Formatter):
    """自定义精细化彩色日志 Formatter：仅高亮日志级别"""

    # 终端颜色 ANSI 转义码
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BOLD_RED = "\033[31;1m"
    BLUE = "\033[34m"
    RESET = "\033[0m"

    # 映射字典：日志级别 -> 颜色
    COLORS = {
        logging.DEBUG: BLUE,
        logging.INFO: GREEN,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: BOLD_RED
    }

    def format(self, record):
        # 1. 备份原始的日志级别名称 (比如 "INFO")
        original_levelname = record.levelname

        # 2. 获取对应的颜色，并将颜色代码包裹在级别名称外
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{original_levelname}{self.RESET}"

        # 3. 调用父类（原生 Formatter）的 format 方法完成最终字符串拼接
        result = super().format(record)

        # 4. 恢复原始的日志级别名称（避免影响其他可能用到该属性的 Handler）
        record.levelname = original_levelname

        return result


# 定义统一的时间戳格式
DATE_FMT = "%Y-%m-%d %H:%M:%S"

# =============================================================================
# 1. 配置控制台的彩色 Formatter
# 由于含有 ANSI 颜色代码（不可见字符），为了视觉对齐，占位宽度设为 -17s
COLOR_LOG_FMT = "%(asctime)s - %(name)s - %(levelname)-17s - %(message)s"
COLOR_FORMATTER = ColorFormatter(fmt=COLOR_LOG_FMT, datefmt=DATE_FMT)

# 控制台 Handler 设置为彩色
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(COLOR_FORMATTER)

# =============================================================================
# 2. 配置文件的普通纯文本 Formatter
# 纯文本没有隐藏的颜色代码，标准的占位宽度设为 -8s 即可完美对齐
PLAIN_LOG_FMT = "%(asctime)s - %(name)s - %(levelname)-8s - %(message)s"
PLAIN_FORMATTER = logging.Formatter(fmt=PLAIN_LOG_FMT, datefmt=DATE_FMT)

# 文件 Handler 设置为普通纯文本（避免记事本打开出现乱码）
file_handler = DailyPathFileHandler(LOG_ROOT, retention_days=30)
file_handler.setFormatter(PLAIN_FORMATTER)

# 1. 配置应用自己的 Logger
app_logger = logging.getLogger("shengyuan_app")
app_logger.setLevel(logging.INFO)
app_logger.propagate = False
if not app_logger.handlers:
    app_logger.addHandler(console_handler)
    app_logger.addHandler(file_handler)

# 2. 配置 SQLAlchemy 日志 (设为 WARNING，屏蔽常规 SQL)
db_logger = logging.getLogger("sqlalchemy.engine")
db_logger.setLevel(logging.WARNING)
db_logger.propagate = False
if not db_logger.handlers:
    db_logger.addHandler(console_handler)
    db_logger.addHandler(file_handler)

# 3. 劫持并重写 Uvicorn 日志
for uvicorn_logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    uv_logger = logging.getLogger(uvicorn_logger_name)
    uv_logger.handlers.clear()  # 清除默认的无时间戳 Handler
    uv_logger.propagate = False
    uv_logger.addHandler(console_handler)
    uv_logger.addHandler(file_handler)

# 导出 app_logger 供其他模块使用
logger = app_logger