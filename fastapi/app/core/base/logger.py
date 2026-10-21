import logging
import os
from datetime import datetime
from typing import Protocol, runtime_checkable

from app.core.config import load_config
from app.core.constants import TelemetryConstants
from app.core.middleware import get_current_trace_id

logger: logging.Logger = logging.getLogger("uvicorn")


@runtime_checkable
class LoggerProtocol(Protocol):
    """日志器协议，供依赖注入时声明类型

    优先通过构造参数注入 LoggerProtocol 实现；无法注入的场景
    （模块级函数、静态方法、装饰器、调度回调等）直接使用全局 Logger 单例
    """

    def info(self, message: str) -> None:
        """记录 INFO 级别日志"""
        ...

    def error(self, message: str) -> None:
        """记录 ERROR 级别日志"""
        ...

    def warning(self, message: str) -> None:
        """记录 WARNING 级别日志"""
        ...

    def debug(self, message: str) -> None:
        """记录 DEBUG 级别日志"""
        ...


def write_log(message: str, level: str = "INFO") -> None:
    """
    直接写入日志到文件

    Args:
        message: 日志消息
        level: 日志级别 (INFO, WARNING, ERROR, DEBUG)
    """
    LOG_PATH: str = load_config("logs")["path"]
    if not os.path.exists(LOG_PATH):
        os.makedirs(LOG_PATH, exist_ok=True)
    log_file: str = os.path.join(
        LOG_PATH, f"app_{datetime.now().strftime('%Y-%m-%d')}.log"
    )
    timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    trace_id: str = get_current_trace_id() or TelemetryConstants.EMPTY_TRACE_ID
    log_entry: str = (
        f"{timestamp} - {level} - "
        f"{TelemetryConstants.TRACE_ID_FIELD}={trace_id} - {message}\n"
    )
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)


def log_info(message: str) -> None:
    """以 INFO 级别同时输出日志到 uvicorn 控制台和当日日志文件"""
    logger.info(message)
    write_log(message, "INFO")


def log_error(message: str) -> None:
    """以 ERROR 级别同时输出日志到 uvicorn 控制台和当日日志文件"""
    logger.error(message)
    write_log(message, "ERROR")


def log_warning(message: str) -> None:
    """以 WARNING 级别同时输出日志到 uvicorn 控制台和当日日志文件"""
    logger.warning(message)
    write_log(message, "WARNING")


def log_debug(message: str) -> None:
    """以 DEBUG 级别同时输出日志到 uvicorn 控制台和当日日志文件"""
    logger.debug(message)
    write_log(message, "DEBUG")


class SimpleLogger:
    """封装各日志级别的简易日志器，同时写入控制台与按日期滚动的日志文件并附带 trace_id"""

    def info(self, message: str) -> None:
        """SimpleLogger 的 info 实现，委托 log_info 输出"""
        log_info(message)

    def error(self, message: str) -> None:
        """SimpleLogger 的 error 实现，委托 log_error 输出"""
        log_error(message)

    def warning(self, message: str) -> None:
        """SimpleLogger 的 warning 实现，委托 log_warning 输出"""
        log_warning(message)

    def debug(self, message: str) -> None:
        """SimpleLogger 的 debug 实现，委托 log_debug 输出"""
        log_debug(message)


Logger: SimpleLogger = SimpleLogger()
