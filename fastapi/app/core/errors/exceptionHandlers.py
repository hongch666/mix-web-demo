from typing import Callable, Dict, List, Type

from app.core.constants import HttpCode, Messages
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from fastapi import Request

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
        Response: JSON 格式的错误响应，使用实际的 HTTP 状态码
    """

    Logger.error(Messages.BUSINESS_EXCEPTION_LOG(request.url, exc.error, exc))
    return JSONResponse(
        status_code=exc.status_code,
        content=error(
            code=exc.status_code,
            msg=exc.message,
        ).model_dump(),
    )


async def global_exception_handler(request: Request, exc: Exception) -> Response:
    """全局异常处理器 - 其他异常统一返回服务器内部错误

    Args:
        request: 请求对象
        exc: 通用异常

    Returns:
        Response: JSON 格式的一般错误响应
    """
    Logger.error(Messages.GLOBAL_EXCEPTION_LOG(request.url, exc))
    return JSONResponse(
        status_code=HttpCode.INTERNAL_SERVER_ERROR,
        content=error(
            code=HttpCode.INTERNAL_SERVER_ERROR,
            msg=Messages.EXCEPTION_HANDLER_MESSAGE,
        ).model_dump(),
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
        else Messages.EXCEPTION_HANDLER_MESSAGE
    )
    Logger.error(Messages.REQUEST_VALIDATION_EXCEPTION_LOG(request.url, validation_message))
    return JSONResponse(
        status_code=HttpCode.BAD_REQUEST,
        content=error(
            code=HttpCode.BAD_REQUEST,
            msg=validation_message,
        ).model_dump(),
    )


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
