"""
Logging configuration for the application
"""
import logging
import sys
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from app.config import settings

# Create logs directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Create logger
logger = logging.getLogger("lumina_api")

# Set log level based on environment
if settings.debug:
    log_level = logging.DEBUG
else:
    log_level = logging.INFO

logger.setLevel(log_level)

# Create formatter with filename and line number
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create handlers if not exists
if not logger.handlers:
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler - general log (rotating by size, 50MB max, keep 5 backups)
    file_handler = RotatingFileHandler(
        LOGS_DIR / "lumina_api.log",
        maxBytes=50*1024*1024,  # 50MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Error log file handler (separate file for errors)
    error_handler = RotatingFileHandler(
        LOGS_DIR / "error.log",
        maxBytes=50*1024*1024,  # 50MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

# Prevent duplicate logs
logger.propagate = False


def cleanup_old_logs(max_size_mb: int = 50):
    """
    清理超过指定大小的日志文件

    Args:
        max_size_mb: 最大文件大小（MB），默认50MB
    """
    try:
        if not LOGS_DIR.exists():
            return

        max_size_bytes = max_size_mb * 1024 * 1024
        deleted_count = 0

        for log_file in LOGS_DIR.glob("*.log*"):
            if log_file.is_file() and log_file.stat().st_size > max_size_bytes:
                try:
                    log_file.unlink()
                    deleted_count += 1
                    logger.info(f"已删除超大日志文件: {log_file.name} ({log_file.stat().st_size / 1024 / 1024:.2f}MB)")
                except Exception as e:
                    logger.error(f"删除日志文件失败 {log_file.name}: {e}")

        if deleted_count > 0:
            logger.info(f"日志清理完成，共删除 {deleted_count} 个文件")

    except Exception as e:
        logger.error(f"清理日志时出错: {e}")


def get_log_size_info():
    """
    获取日志目录大小信息

    Returns:
        dict: 包含日志文件数量和总大小
    """
    try:
        if not LOGS_DIR.exists():
            return {"file_count": 0, "total_size_mb": 0}

        total_size = 0
        file_count = 0

        for log_file in LOGS_DIR.glob("*.log*"):
            if log_file.is_file():
                total_size += log_file.stat().st_size
                file_count += 1

        return {
            "file_count": file_count,
            "total_size_mb": round(total_size / 1024 / 1024, 2)
        }
    except Exception as e:
        logger.error(f"获取日志大小信息时出错: {e}")
        return {"file_count": 0, "total_size_mb": 0}

