from fastapi import APIRouter

from client.client import call_remote_service
from utils.response import success

router = APIRouter(
    prefix="/api_fastapi",
    tags=["测试接口"],
)

# 测试
@router.get("/fastapi")
def testFastapi():
    return success("Hello, I am FastAPI!")

# 测试Spring服务
@router.get("/spring")
def testSpring():
    """ headers = {"Authorization": "Bearer xxx"}
    body = {"foo": "bar", "list": [1, 2, 3]} """
    result = call_remote_service(
        service_name="spring",
        path="/api_spring/spring",
        method="GET",
        retries=2
    )
    return success(result["data"])

# 测试Gin服务
@router.get("/gin")
def testGin():
    result = call_remote_service(
        service_name="gin",
        path="/api_gin/gin",
        method="GET",
        retries=2
    )
    return success(result["data"])

# 测试NestJS服务
@router.get("/nestjs")
def testNestJS():
    result = call_remote_service(
        service_name="nestjs",
        path="/api_nestjs/nestjs",
        method="GET",
        retries=2
    )
    return success(result["data"])