from typing import Annotated

from fastapi import Depends

from app.core.base import Logger, LoggerProtocol


def provide_logger() -> LoggerProtocol:
    """提供日志器依赖

    当前返回进程级单例 Logger，作为可替换的注入点；
    需要按请求或按模块差异化日志行为时，仅需调整本 provider 的实现
    """
    return Logger


LoggerDep = Annotated[LoggerProtocol, Depends(provide_logger)]
