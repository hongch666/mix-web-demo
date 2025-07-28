from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import Any, Dict

from common.client.client import call_remote_service
from common.utils.response import success
from common.middleware.ContextMiddleware import get_current_user_id, get_current_username
from common.utils.writeLog import fileLogger

router: APIRouter = APIRouter(
    prefix="/api_fastapi",
    tags=["测试接口"],
)

# 测试
@router.get("/fastapi")
async def testFastapi() -> JSONResponse:
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    fileLogger.info("用户" + user_id + ":" + username + " GET /api_fastapi/fastapi: 测试FastAPI服务")
    return success("Hello, I am FastAPI!") # type: ignore

# 测试Spring服务
@router.get("/spring")
async def testSpring() -> JSONResponse:
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    fileLogger.info("用户" + user_id + ":" + username + " GET /api_fastapi/spring: 测试Spring服务")
    result: Dict[str, Any] = await call_remote_service(
        service_name="spring",
        path="/api_spring/spring",
        method="GET",
        retries=2
    )
    return success(result["data"]) # type: ignore

# 测试Gin服务
@router.get("/gin")
async def testGin() -> JSONResponse:
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    fileLogger.info("用户" + user_id + ":" + username + " GET /api_fastapi/gin: 测试Gin服务")
    result: Dict[str, Any] = await call_remote_service(
        service_name="gin",
        path="/api_gin/gin",
        method="GET",
        retries=2
    )
    return success(result["data"]) # type: ignore

# 测试NestJS服务
@router.get("/nestjs")
async def testNestJS() -> JSONResponse:
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    fileLogger.info("用户" + user_id + ":" + username + " GET /api_fastapi/nestjs: 测试NestJS服务")
    result: Dict[str, Any] = await call_remote_service(
        service_name="nestjs",
        path="/api_nestjs/nestjs",
        method="GET",
        retries=2
    )
    return success(result["data"]) # type: ignore