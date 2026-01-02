from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from typing import Any, Dict
from common.decorators import log
from common.client import call_remote_service
from common.task import (
    export_articles_to_csv_and_hive, 
    export_article_vectors_to_postgres, 
    initialize_article_content_hash_cache
)
from common.utils import success,fail,fileLogger as logger

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
    """测试FastAPI服务接口"""
    
    return success("Hello, I am FastAPI!")

# 测试Spring服务
@router.get(
    "/spring",
    summary="测试Spring服务",
    description="测试Spring服务"
)
@log("测试Spring服务")
async def testSpring(request: Request) -> JSONResponse:
    """测试Spring服务接口"""
    
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
    """测试Gin服务接口"""
    
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
    """测试NestJS服务接口"""
    
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
    description="手动触发文章表导出到hive的定时任务"
)
@log("手动触发文章表导出任务")
async def test_export_articles_task(request: Request) -> JSONResponse:
    """手动触发文章表导出任务接口"""
    
    try:
        await run_in_threadpool(export_articles_to_csv_and_hive)
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
    """手动触发向量数据库同步任务接口"""
    
    try:
        await run_in_threadpool(export_article_vectors_to_postgres)
        return success()
    except Exception as e:
        logger.error(f"手动触发向量数据库同步任务失败: {e}")
        return fail(f"任务执行失败: {e}")

@router.post(
    "/task/init-hash-cache",
    summary="初始化文章内容 hash 缓存",
    description="为所有已发布的文章初始化内容 hash 缓存。用于生产环境已有大量文章和向量库数据，但缺少 hash 缓存的场景。此操作只生成 hash，不进行向量同步。"
)
@log("初始化文章内容 hash 缓存")
async def test_init_hash_cache_task(request: Request) -> JSONResponse:
    """初始化文章内容 hash 缓存接口"""
    
    try:
        await run_in_threadpool(initialize_article_content_hash_cache)
        return success("文章内容 hash 缓存初始化完成")
    except Exception as e:
        logger.error(f"初始化文章内容 hash 缓存失败: {e}")
        return fail(f"任务执行失败: {e}")