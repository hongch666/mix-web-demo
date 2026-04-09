from typing import Any, Dict

from app.common.decorators import log, requireInternalToken
from app.core.base import Constants, Logger, success
from app.internal.cache import (
    get_article_cache,
    get_category_cache,
    get_publish_time_cache,
    get_statistics_cache,
    get_wordcloud_cache,
)
from app.internal.services import (
    call_remote_service,
    export_article_vectors_to_postgres,
    initialize_article_content_hash_cache,
    update_analyze_caches,
)
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from fastapi import APIRouter, Request

router: APIRouter = APIRouter(
    prefix="/api_fastapi",
    tags=["测试接口"],
)


# 测试
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


@router.post(
    "/task/update-analyze-caches",
    summary="更新分析接口缓存",
    description="手动触发更新分析接口缓存的定时任务",
)
@requireInternalToken
@log("手动触发更新分析接口缓存任务")
async def test_update_analyze_caches_task(request: Request) -> JSONResponse:
    """手动触发更新分析接口缓存任务接口"""

    await run_in_threadpool(update_analyze_caches)
    return success()


@router.post(
    "/task/vector",
    summary="手动触发向量数据库同步任务",
    description="手动触发同步文章数据PostgreSQL向量数据库的定时任务",
)
@requireInternalToken
@log("手动触发向量数据库同步任务")
async def test_export_vector_task(request: Request) -> JSONResponse:
    """手动触发向量数据库同步任务接口"""

    await run_in_threadpool(export_article_vectors_to_postgres)
    return success()


@router.post(
    "/task/init-hash-cache",
    summary="初始化文章内容 hash 缓存",
    description="为所有已发布的文章初始化内容 hash 缓存。用于生产环境已有大量文章和向量库数据，但缺少 hash 缓存的场景。此操作只生成 hash，不进行向量同步。",
)
@requireInternalToken
@log("初始化文章内容 hash 缓存")
async def test_init_hash_cache_task(request: Request) -> JSONResponse:
    """初始化文章内容 hash 缓存接口"""

    await run_in_threadpool(initialize_article_content_hash_cache)
    return success()


@router.post(
    "/task/clear-analyze-caches",
    summary="清除分析相关缓存",
    description="删除所有文章分析相关的缓存数据（包括 Top10、分类统计、月度统计、词云、统计信息等），用于远程触发缓存更新",
)
@requireInternalToken
@log("清除分析相关缓存")
async def clear_analyze_caches_task(request: Request) -> JSONResponse:
    """清除所有分析相关缓存接口"""

    # 获取所有分析相关的缓存对象
    async def clear_caches() -> None:
        caches_info = []

        # 清除 Top10 文章缓存
        try:
            article_cache = get_article_cache()
            await article_cache.clear_all()
            caches_info.append("Top10 文章缓存")
        except Exception as e:
            Logger.warning(f"清除 Top10 文章缓存失败: {e}")

        # 清除 分类统计缓存
        try:
            category_cache = get_category_cache()
            await category_cache.clear_all()
            caches_info.append("分类统计缓存")
        except Exception as e:
            Logger.warning(f"清除分类统计缓存失败: {e}")

        # 清除 月度发布统计缓存
        try:
            publish_time_cache = get_publish_time_cache()
            await publish_time_cache.clear_all()
            caches_info.append("月度发布统计缓存")
        except Exception as e:
            Logger.warning(f"清除月度发布统计缓存失败: {e}")

        # 清除 统计信息缓存
        try:
            statistics_cache = get_statistics_cache()
            await statistics_cache.clear_all()
            caches_info.append("统计信息缓存")
        except Exception as e:
            Logger.warning(f"清除统计信息缓存失败: {e}")

        # 清除 词云缓存
        try:
            wordcloud_cache = get_wordcloud_cache()
            await wordcloud_cache.delete()
            caches_info.append("词云缓存")
        except Exception as e:
            Logger.warning(f"清除词云缓存失败: {e}")

        if caches_info:
            Logger.info(f"成功清除以下缓存: {', '.join(caches_info)}")

    await clear_caches()
    return success()
