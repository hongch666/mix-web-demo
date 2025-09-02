import os
from datetime import datetime
from typing import Any


def _get_logger():
    # lazy import to avoid circular import with package-level imports
    try:
        from .loggers import logger
        return logger
    except Exception:
        import logging
        return logging.getLogger('app')


def write_log(message: str, level: str = "INFO") -> None:
    """
    直接写入日志到文件
    
    Args:
        message: 日志消息
        level: 日志级别 (INFO, WARNING, ERROR, DEBUG)
    """
    # lazy import load_config to avoid import-time circular dependency with config/nacos
    from config import load_config
    LOG_PATH: str = load_config("logs")["path"]
    if not os.path.exists(LOG_PATH):
        os.makedirs(LOG_PATH, exist_ok=True)
    log_file: str = os.path.join(LOG_PATH, f"app_{datetime.now().strftime('%Y-%m-%d')}.log")
    timestamp: str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry: str = f"{timestamp} - {level} - {message}\n"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)

def log_info(message: str) -> None:
    _get_logger().info(message)
    write_log(message, "INFO")

def log_error(message: str) -> None:
    _get_logger().error(message)
    write_log(message, "ERROR")

def log_warning(message: str) -> None:
    _get_logger().warning(message)
    write_log(message, "WARNING")

def log_debug(message: str) -> None:
    _get_logger().debug(message)
    write_log(message, "DEBUG")

class SimpleLogger:
    def info(self, message: str) -> None:
        log_info(message)
    
    def error(self, message: str) -> None:
        log_error(message)
    
    def warning(self, message: str) -> None:
        log_warning(message)
    
    def debug(self, message: str) -> None:
        log_debug(message)

fileLogger: SimpleLogger = SimpleLogger()
