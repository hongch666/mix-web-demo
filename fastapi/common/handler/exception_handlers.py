from fastapi import Request
from fastapi.responses import JSONResponse
from common.utils.response import fail

async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content= fail(str(exc))
    )