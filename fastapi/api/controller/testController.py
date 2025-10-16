from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from typing import Any, Dict
from common.decorators import log
from common.client import call_remote_service
from common.task import export_articles_to_csv_and_hive, export_article_vectors_to_postgres
from common.utils import success,fail,fileLogger

router: APIRouter = APIRouter(
    prefix="/api_fastapi",
    tags=["测试接口"],
)

# 测试
@router.get("/fastapi")
@log("测试FastAPI服务")
async def testFastapi(request: Request) -> JSONResponse:
    return success("Hello, I am FastAPI!")

# 测试Spring服务
@router.get("/spring")
@log("测试Spring服务")
async def testSpring(request: Request) -> JSONResponse:
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
async def testGin(request: Request) -> JSONResponse:
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
async def testNestJS(request: Request) -> JSONResponse:
    result: Dict[str, Any] = await call_remote_service(
        service_name="nestjs",
        path="/api_nestjs/nestjs",
        method="GET",
        retries=2
    )
    return success(result["data"])

# 调用定时任务（导出文章表到csv并同步hive）
@router.post("/task/hive")
@log("手动触发文章表导出任务")
async def test_export_articles_task(request: Request) -> JSONResponse:
    try:
        export_articles_to_csv_and_hive()
        return success()
    except Exception as e:
        fileLogger.error(f"手动触发文章表导出任务失败: {e}")
        return fail(f"任务执行失败: {e}")
    
# 调用定时任务（导出文章表到csv并同步hive）
@router.post("/task/vector")
@log("手动触发向量数据库同步任务")
async def test_export_articles_task(request: Request) -> JSONResponse:
    try:
        export_article_vectors_to_postgres()
        return success()
    except Exception as e:
        fileLogger.error(f"手动触发向量数据库同步任务失败: {e}")
        return fail(f"任务执行失败: {e}")