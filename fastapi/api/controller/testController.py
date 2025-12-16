from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from typing import Any, Dict
from common.decorators import log
from common.client import call_remote_service
from common.task import export_articles_to_csv_and_hive, export_article_vectors_to_postgres
from common.utils import success,fail,fileLogger as logger
from common.cache import ArticleCache, CategoryCache, PublishTimeCache, StatisticsCache, get_article_cache, get_category_cache, get_publish_time_cache, get_statistics_cache

router: APIRouter = APIRouter(
    prefix="/api_fastapi",
    tags=["测试接口"],
)

# 测试
@router.get(
    "/fastapi", 
    summary="测试FastAPI服务", 
    description="测试FastAPI服务"
)
@log("测试FastAPI服务")
async def testFastapi(request: Request) -> JSONResponse:
    return success("Hello, I am FastAPI!")

# 测试Spring服务
@router.get(
    "/spring",
    summary="测试Spring服务",
    description="测试Spring服务"
)
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
@router.get(
    "/gin",
    summary="测试Gin服务",
    description="测试Gin服务"
)
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
@router.get(
    "/nestjs",
    summary="测试NestJS服务",
    description="测试NestJS服务"
)
@log("测试NestJS服务")
async def testNestJS(request: Request) -> JSONResponse:
    result: Dict[str, Any] = await call_remote_service(
        service_name="nestjs",
        path="/api_nestjs/nestjs",
        method="GET",
        retries=2
    )
    return success(result["data"])

@router.post(
    "/task/hive",
    summary="手动触发文章表导出任务",
    description="手动触发文章表导出到hive的定时任务，并清除所有缓存（top10、分类文章数、月份文章数、统计信息）"
)
@log("手动触发文章表导出任务")
async def test_export_articles_task(request: Request, article_cache: ArticleCache = Depends(get_article_cache), category_cache: CategoryCache = Depends(get_category_cache), publish_time_cache: PublishTimeCache = Depends(get_publish_time_cache), statistics_cache: StatisticsCache = Depends(get_statistics_cache)) -> JSONResponse:
    try:
        await run_in_threadpool(export_articles_to_csv_and_hive)
        # 清除所有相关缓存
        article_cache.clear_all()
        category_cache.clear_all()
        publish_time_cache.clear_all()
        statistics_cache.clear_all()
        logger.info("已清除所有缓存: top10文章、分类文章数、月份文章数、统计信息")
        return success()
    except Exception as e:
        logger.error(f"手动触发文章表导出任务失败: {e}")
        return fail(f"任务执行失败: {e}")
    
@router.post(
    "/task/vector",
    summary="手动触发向量数据库同步任务",
    description="手动触发同步文章数据PostgreSQL向量数据库的定时任务"
)
@log("手动触发向量数据库同步任务")
async def test_export_vector_task(request: Request) -> JSONResponse:
    try:
        await run_in_threadpool(export_article_vectors_to_postgres)
        return success()
    except Exception as e:
        logger.error(f"手动触发向量数据库同步任务失败: {e}")
        return fail(f"任务执行失败: {e}")