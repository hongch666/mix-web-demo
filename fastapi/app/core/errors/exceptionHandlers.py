from typing import Callable, Dict, List, Type

from fastapi.responses import JSONResponse, Response

from app.core.base.constants import Constants
from app.core.base.response import error
from app.core.base.writeLog import Logger
from app.core.errors.exceptions import BusinessException
from fastapi import Request


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


exception_handlers: Dict[Type[Exception], Callable] = {
    BusinessException: business_exception_handler,
    Exception: global_exception_handler,
}

__all__: List[str] = [
    "global_exception_handler",
    "business_exception_handler",
    "exception_handlers",
]
