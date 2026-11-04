import logging
import os
from datetime import datetime
from logging import Handler
from typing import Any, Protocol, runtime_checkable

from app.core.config import load_config
from app.core.constants import TelemetryConstants
from app.core.middleware import get_current_trace_id

logger: logging.Logger = logging.getLogger("uvicorn")

# 文件日志独立命名空间，避免与 uvicorn 自身的 handler 互相影响
file_logger: logging.Logger = logging.getLogger("mix.file")

# 文件日志句柄与对应配置签名，按日期与配置复用，避免每行日志都重新打开文件
_file_handler: Handler | None = None
_file_handler_state: tuple[str, bool, str, str] | None = None

_LEVEL_NAMES: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}


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


class _TraceIdFormatter(logging.Formatter):
    """把当前请求的 trace_id 注入日志行的文件日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """格式化前补上 trace_id 字段，缺失时使用空值占位"""
        record.trace_id = get_current_trace_id() or TelemetryConstants.EMPTY_TRACE_ID
        return super().format(record)


def _logs_config() -> dict[str, Any]:
    """读取 logs 配置段，读取失败时返回空配置，避免日志本身抛出异常"""
    try:
        return load_config("logs") or {}
    except Exception:
        return {}


def _build_formatter(include_timestamp: bool) -> logging.Formatter:
    """按是否输出时间戳构造文件日志格式，保持与原逐行写文件一致的文本形态"""
    if include_timestamp:
        return _TraceIdFormatter(
            "%(asctime)s - %(levelname)s - trace_id=%(trace_id)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    return _TraceIdFormatter("%(levelname)s - trace_id=%(trace_id)s - %(message)s")


def _ensure_file_handler(logs_config: dict[str, Any]) -> Handler | None:
    """按当日日期与配置复用文件句柄，配置或日期变化时重新打开文件"""
    global _file_handler, _file_handler_state

    log_path: str = str(logs_config.get("path") or "")
    if not log_path:
        return None

    # 容器部署关闭行内时间戳，时间由 Loki 采集侧提供，避免同一行出现两个日期
    include_timestamp: bool = (
        str(logs_config.get("include_timestamp", True)).strip().lower() != "false"
    )
    level_name: str = (
        str(logs_config.get("file_level") or "INFO").strip().upper() or "INFO"
    )
    today: str = datetime.now().strftime("%Y-%m-%d")
    state: tuple[str, bool, str, str] = (log_path, include_timestamp, level_name, today)
    if _file_handler is not None and _file_handler_state == state:
        return _file_handler

    if not os.path.exists(log_path):
        os.makedirs(log_path, exist_ok=True)
    log_file: str = os.path.join(log_path, f"app_{today}.log")

    if _file_handler is not None:
        file_logger.removeHandler(_file_handler)
        _file_handler.close()
        _file_handler = None

    handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    handler.setFormatter(_build_formatter(include_timestamp))
    file_logger.addHandler(handler)
    file_logger.setLevel(_LEVEL_NAMES.get(level_name, logging.INFO))
    file_logger.propagate = False
    _file_handler = handler
    _file_handler_state = state
    return handler


def write_log(message: str, level: str = "INFO") -> None:
    """
    直接写入日志到文件

    文件句柄与配置按进程复用，低于配置的文件级别时由 logging 直接丢弃，
    避免高频调试日志（如逐键缓存命中）产生逐行读盘与写文件开销

    Args:
        message: 日志消息
        level: 日志级别 (INFO, WARNING, ERROR, DEBUG)
    """
    if _ensure_file_handler(_logs_config()) is None:
        return
    file_logger.log(_LEVEL_NAMES.get(level.upper(), logging.INFO), message)


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
