from common.exceptions import BusinessException

from .exceptionHandlers import business_exception_handler, global_exception_handler

# 异常处理器映射
exception_handlers: dict = {
    BusinessException: business_exception_handler,
    Exception: global_exception_handler,
}

__all__: list[str] = [
    "global_exception_handler",
    "business_exception_handler",
    "exception_handlers",
]
