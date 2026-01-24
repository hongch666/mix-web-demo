from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.responses import Response
from common.utils import error, fileLogger as logger, Constants
from common.exceptions import BusinessException

async def business_exception_handler(request: Request, exc: BusinessException) -> Response:
    """业务异常处理器 - 返回客户端可见的错误信息"""
    logger.error(f"请求路径: {request.url}，业务错误: {str(exc)}")
    return JSONResponse(
        status_code=200,
        content=error(exc.message)
    )

async def global_exception_handler(request: Request, exc: Exception) -> Response:
    """全局异常处理器 - 其他异常统一返回服务器内部错误"""
    logger.error(f"请求路径: {request.url}，错误信息: {str(exc)}")
    return JSONResponse(
        status_code=200,
        content=error(Constants.EXCEPTION_HANDLER_MESSAGE)
    )