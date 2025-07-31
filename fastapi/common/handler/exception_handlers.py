from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.responses import Response
from common.utils import fail
from typing import Any

async def global_exception_handler(request: Request, exc: Exception) -> Response:
    return JSONResponse(
        status_code=500,
        content=fail(str(exc))
    )