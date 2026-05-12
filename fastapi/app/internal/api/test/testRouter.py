from typing import Any, Dict

from app.common.decorators import log, requireInternalToken
from app.core.base import Constants, success
from app.core.client import call_remote_service
from app.internal.cache import (
    get_article_cache,
    get_category_cache,
    get_publish_time_cache,
    get_statistics_cache,
    get_wordcloud_cache,
)
from app.internal.tasks import (
    export_article_vectors_to_postgres_async,
    initialize_article_content_hash_cache_async,
    sync_mysql_to_neo4j_async,
    update_analyze_caches_async,
)
from fastapi.responses import JSONResponse

from fastapi import APIRouter, Request

router: APIRouter = APIRouter(
    prefix="/api_fastapi",
    tags=["测试模块"],
)


# 测试FastAPI服务
@router.get("/fastapi", summary="测试FastAPI服务", description="测试FastAPI服务")
@log("测试FastAPI服务")
async def testFastapi(request: Request) -> JSONResponse:
    """测试FastAPI服务接口"""
    return success(Constants.TEST_MESSAGE)


# 测试Spring服务
@router.get("/spring", summary="测试Spring服务", description="测试Spring服务")
@log("测试Spring服务")
async def testSpring(request: Request) -> JSONResponse:
    """测试Spring服务接口"""

    result: Dict[str, Any] = await call_remote_service(
        service_name="spring", path="/api_spring/spring", method="GET", retries=2
    )
    return success(result["data"])


# 测试GoZero服务
@router.get("/gozero", summary="测试GoZero服务", description="测试GoZero服务")
@log("测试GoZero服务")
async def testGoZero(request: Request) -> JSONResponse:
    """测试GoZero服务接口"""

    result: Dict[str, Any] = await call_remote_service(
        service_name="gozero", path="/api_gozero/gozero", method="GET", retries=2
    )
    return success(result["data"])


# 测试NestJS服务
@router.get("/nestjs", summary="测试NestJS服务", description="测试NestJS服务")
@log("测试NestJS服务")
async def testNestJS(request: Request) -> JSONResponse:
    """测试NestJS服务接口"""

    result: Dict[str, Any] = await call_remote_service(
        service_name="nestjs", path="/api_nestjs/nestjs", method="GET", retries=2
    )
    return success(result["data"])


# 手动触发更新分析接口缓存定时任务接口
@router.post(
    "/task/update-analyze-caches",
    summary="更新分析接口缓存",
    description="手动触发更新分析接口缓存的定时任务",
)
@requireInternalToken
@log("手动触发更新分析接口缓存任务")
async def test_update_analyze_caches_task(request: Request) -> JSONResponse:
    """手动触发更新分析接口缓存任务接口"""

    await update_analyze_caches_async()
    return success()


# 手动触发向量数据库同步任务接口
@router.post(
    "/task/vector",
    summary="手动触发向量数据库同步任务",
    description="手动触发同步文章数据PostgreSQL向量数据库的定时任务",
)
@requireInternalToken
@log("手动触发向量数据库同步任务")
async def test_export_vector_task(request: Request) -> JSONResponse:
    """手动触发向量数据库同步任务接口"""

    await export_article_vectors_to_postgres_async()
    return success()


# 手动触发初始化文章内容 hash 缓存任务接口
@router.post(
    "/task/init-hash-cache",
    summary="初始化文章内容 hash 缓存",
    description="为所有已发布的文章初始化内容 hash 缓存。用于生产环境已有大量文章和向量库数据，但缺少 hash 缓存的场景。此操作只生成 hash，不进行向量同步。",
)
@requireInternalToken
@log("初始化文章内容 hash 缓存")
async def test_init_hash_cache_task(request: Request) -> JSONResponse:
    """初始化文章内容 hash 缓存接口"""

    await initialize_article_content_hash_cache_async()
    return success()


# 手动触发清除分析相关缓存任务接口
@router.post(
    "/task/clear-analyze-caches",
    summary="清除分析相关缓存",
    description="删除所有文章分析相关的缓存数据（包括 Top10、分类统计、月度统计、词云、统计信息等），用于远程触发缓存更新",
)
@requireInternalToken
@log("清除分析相关缓存")
async def clear_analyze_caches_task(request: Request) -> JSONResponse:
    """清除所有分析相关缓存接口"""

    article_cache = get_article_cache()
    await article_cache.clear_all()

    category_cache = get_category_cache()
    await category_cache.clear_all()

    publish_time_cache = get_publish_time_cache()
    await publish_time_cache.clear_all()

    statistics_cache = get_statistics_cache()
    await statistics_cache.clear_all()

    wordcloud_cache = get_wordcloud_cache()
    await wordcloud_cache.delete()

    return success()


# 手动触发同步 MySQL 到 Neo4j 知识图谱任务接口
@router.post(
    "/task/sync-neo4j",
    summary="手动触发同步 MySQL 到 Neo4j 知识图谱任务",
    description="手动触发同步 MySQL 数据到 Neo4j 知识图谱的定时任务",
)
@requireInternalToken
@log("手动触发同步 MySQL 到 Neo4j 知识图谱任务")
async def test_sync_neo4j_task(request: Request) -> JSONResponse:
    """手动触发同步 MySQL 到 Neo4j 知识图谱任务接口"""

    await sync_mysql_to_neo4j_async()
    return success()
