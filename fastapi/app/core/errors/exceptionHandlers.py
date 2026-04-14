from typing import Callable, Dict, List, Type

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from fastapi import Request

from ..base.constants import Constants
from ..base.response import error
from ..base.writeLog import Logger
from .exceptions import BusinessException


async def business_exception_handler(
    request: Request, exc: BusinessException
) -> Response:
    """业务异常处理器 - 返回客户端可见的错误信息

    Args:
        request: 请求对象
        exc: 业务异常

    Returns:
        Response: JSON 格式的错误响应
    """
    Logger.error(f"请求路径: {request.url}，业务错误: {str(exc)}")
    return JSONResponse(status_code=200, content=error(exc.message))


async def global_exception_handler(request: Request, exc: Exception) -> Response:
    """全局异常处理器 - 其他异常统一返回服务器内部错误

    Args:
        request: 请求对象
        exc: 通用异常

    Returns:
        Response: JSON 格式的一般错误响应
    """
    Logger.error(f"请求路径: {request.url}，错误信息: {str(exc)}")
    return JSONResponse(
        status_code=200, content=error(Constants.EXCEPTION_HANDLER_MESSAGE)
    )


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> Response:
    """请求校验异常处理器 - 将字段校验错误统一返回为项目格式

    Args:
        request: 请求对象
        exc: 请求校验异常

    Returns:
        Response: JSON 格式的错误响应
    """

    validation_message_parts: List[str] = []
    for item in exc.errors():
        message = item.get("msg")
        if message:
            validation_message_parts.append(str(message))

    validation_message = (
        "; ".join(validation_message_parts)
        if validation_message_parts
        else Constants.EXCEPTION_HANDLER_MESSAGE
    )
    Logger.error(f"请求路径: {request.url}，校验错误: {validation_message}")
    return JSONResponse(status_code=200, content=error(validation_message))


exception_handlers: Dict[Type[Exception], Callable] = {
    BusinessException: business_exception_handler,
    RequestValidationError: request_validation_exception_handler,
    Exception: global_exception_handler,
}

__all__: List[str] = [
    "global_exception_handler",
    "business_exception_handler",
    "request_validation_exception_handler",
    "exception_handlers",
]
