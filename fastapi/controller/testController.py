from fastapi import APIRouter

from client.client import call_remote_service
from utils.response import success
from utils.logger import logger
from middleware.ContextMiddleware import get_current_user_id, get_current_username

router = APIRouter(
    prefix="/api_fastapi",
    tags=["测试接口"],
)

# 测试
@router.get("/fastapi")
async def testFastapi():
    user_id = get_current_user_id() or ""
    username = get_current_username() or ""
    logger.info("用户"+user_id+":"+username+" GET /api_fastapi/fastapi: 测试FastAPI服务")
    return success("Hello, I am FastAPI!")

# 测试Spring服务
@router.get("/spring")
async def testSpring():
    logger.info("GET /api_fastapi/spring: 测试Spring服务")
    """ headers = {"Authorization": "Bearer xxx"}
    body = {"foo": "bar", "list": [1, 2, 3]} """
    result = await call_remote_service(
        service_name="spring",
        path="/api_spring/spring",
        method="GET",
        retries=2
    )
    return success(result["data"])

# 测试Gin服务
@router.get("/gin")
async def testGin():
    logger.info("GET /api_fastapi/gin: 测试Gin服务")
    result = await call_remote_service(
        service_name="gin",
        path="/api_gin/gin",
        method="GET",
        retries=2
    )
    return success(result["data"])

# 测试NestJS服务
@router.get("/nestjs")
async def testNestJS():
    logger.info("GET /api_fastapi/nestjs: 测试NestJS服务")
    result = await call_remote_service(
        service_name="nestjs",
        path="/api_nestjs/nestjs",
        method="GET",
        retries=2
    )
    return success(result["data"])