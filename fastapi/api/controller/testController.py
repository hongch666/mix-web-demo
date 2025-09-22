from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import Any, Dict

from common.decorators import log
from common.client import call_remote_service
from common.task import export_articles_to_csv_and_hive
from common.utils import success,fail,fileLogger

router: APIRouter = APIRouter(
    prefix="/api_fastapi",
    tags=["测试接口"],
)

# 测试
@router.get("/fastapi")
@log("测试FastAPI服务")
async def testFastapi() -> JSONResponse:
    return success("Hello, I am FastAPI!")

# 测试Spring服务
@router.get("/spring")
@log("测试Spring服务")
async def testSpring() -> JSONResponse:
    result: Dict[str, Any] = await call_remote_service(
        service_name="spring",
        path="/api_spring/spring",
        method="GET",
        retries=2
    )
    return success(result["data"])

# 测试Gin服务
@router.get("/gin")
@log("测试Gin服务")
async def testGin() -> JSONResponse:
    result: Dict[str, Any] = await call_remote_service(
        service_name="gin",
        path="/api_gin/gin",
        method="GET",
        retries=2
    )
    return success(result["data"])

# 测试NestJS服务
@router.get("/nestjs")
@log("测试NestJS服务")
async def testNestJS() -> JSONResponse:
    result: Dict[str, Any] = await call_remote_service(
        service_name="nestjs",
        path="/api_nestjs/nestjs",
        method="GET",
        retries=2
    )
    return success(result["data"])

# 调用定时任务（导出文章表到csv并同步hive）
@router.post("/task")
@log("手动触发文章表导出任务")
async def test_export_articles_task() -> JSONResponse:
    try:
        export_articles_to_csv_and_hive()
        return success()
    except Exception as e:
        fileLogger.error(f"手动触发文章表导出任务失败: {e}")
        return fail(f"任务执行失败: {e}")