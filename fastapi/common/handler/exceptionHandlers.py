from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.responses import Response
from common.utils import fail,fileLogger as logger
from typing import Any

async def global_exception_handler(request: Request, exc: Exception) -> Response:
    logger.error(f"请求路径: {request.url}，错误信息: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=fail(str(exc))
    )