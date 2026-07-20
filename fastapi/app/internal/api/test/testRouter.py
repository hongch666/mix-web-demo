from typing import Any, Dict

from app.common.decorators import log
from app.core.base import success
from app.core.constants import Messages
from app.internal.clients import GoZeroClient, NestjsClient, SpringClient
from fastapi.responses import JSONResponse

from fastapi import APIRouter, Request

router: APIRouter = APIRouter(
    prefix="/api_fastapi",
    tags=["测试模块"],
)

# 初始化客户端实例
spring_client: SpringClient = SpringClient()
gozero_client: GoZeroClient = GoZeroClient()
nestjs_client: NestjsClient = NestjsClient()


# 测试FastAPI服务
@router.get("/fastapi", summary="测试FastAPI服务", description="测试FastAPI服务")
@log("测试FastAPI服务")
async def testFastapi(request: Request) -> JSONResponse:
    """测试FastAPI服务接口"""
    return success(Messages.TEST_MESSAGE)


# 测试Spring服务
@router.get("/spring", summary="测试Spring服务", description="测试Spring服务")
@log("测试Spring服务")
async def testSpring(request: Request) -> JSONResponse:
    """测试Spring服务接口"""

    result: Dict[str, Any] = await spring_client.test()
    return success(result.get("data"))


# 测试GoZero服务
@router.get("/gozero", summary="测试GoZero服务", description="测试GoZero服务")
@log("测试GoZero服务")
async def testGoZero(request: Request) -> JSONResponse:
    """测试GoZero服务接口"""

    result: Dict[str, Any] = await gozero_client.test()
    return success(result.get("data"))


# 测试NestJS服务
@router.get("/nestjs", summary="测试NestJS服务", description="测试NestJS服务")
@log("测试NestJS服务")
async def testNestJS(request: Request) -> JSONResponse:
    """测试NestJS服务接口"""

    result: Dict[str, Any] = await nestjs_client.test()
    return success(result.get("data"))

