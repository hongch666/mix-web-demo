import asyncio

from app.common.decorators import log, requireInternalToken
from app.core.base import success
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

from fastapi import APIRouter, BackgroundTasks, Request

router: APIRouter = APIRouter(
    prefix="/task",
    tags=["定时任务模块"],
)


# 手动触发更新分析接口缓存定时任务接口
@router.post(
    "/update-analyze-caches",
    summary="更新分析接口缓存",
    description="手动触发更新分析接口缓存的定时任务",
)
@requireInternalToken
@log("手动触发更新分析接口缓存任务")
async def task_update_analyze_caches(
    request: Request, background_tasks: BackgroundTasks
) -> JSONResponse:
    """手动触发更新分析接口缓存任务接口"""

    background_tasks.add_task(update_analyze_caches_async)
    return success()


# 手动触发向量数据库同步任务接口
@router.post(
    "/vector",
    summary="手动触发向量数据库同步任务",
    description="手动触发同步文章数据PostgreSQL向量数据库的定时任务",
)
@requireInternalToken
@log("手动触发向量数据库同步任务")
async def task_export_vector(
    request: Request, background_tasks: BackgroundTasks
) -> JSONResponse:
    """手动触发向量数据库同步任务接口"""

    background_tasks.add_task(export_article_vectors_to_postgres_async)
    return success()


# 手动触发初始化文章内容 hash 缓存任务接口
@router.post(
    "/init-hash-cache",
    summary="初始化文章内容 hash 缓存",
    description="为所有已发布的文章初始化内容 hash 缓存。用于生产环境已有大量文章和向量库数据，但缺少 hash 缓存的场景。此操作只生成 hash，不进行向量同步。",
)
@requireInternalToken
@log("初始化文章内容 hash 缓存")
async def task_init_hash_cache(request: Request) -> JSONResponse:
    """初始化文章内容 hash 缓存接口"""

    await initialize_article_content_hash_cache_async()
    return success()


# 手动触发清除分析相关缓存任务接口
@router.post(
    "/clear-analyze-caches",
    summary="清除分析相关缓存",
    description="删除所有文章分析相关的缓存数据（包括 Top10、分类统计、月度统计、词云、统计信息等），用于远程触发缓存更新",
)
@requireInternalToken
@log("清除分析相关缓存")
async def task_clear_analyze_caches(
    request: Request, background_tasks: BackgroundTasks
) -> JSONResponse:
    """清除所有分析相关缓存接口"""

    async def _clear_caches() -> None:
        # 5个缓存清除操作相互独立，gather 并行降低延迟
        await asyncio.gather(
            get_article_cache().clear_all(),
            get_category_cache().clear_all(),
            get_publish_time_cache().clear_all(),
            get_statistics_cache().clear_all(),
            get_wordcloud_cache().delete(),
        )

    background_tasks.add_task(_clear_caches)
    return success()


# 手动触发同步 MySQL 到 Neo4j 知识图谱任务接口
@router.post(
    "/sync-neo4j",
    summary="手动触发同步 MySQL 到 Neo4j 知识图谱任务",
    description="手动触发同步 MySQL 数据到 Neo4j 知识图谱的定时任务",
)
@requireInternalToken
@log("手动触发同步 MySQL 到 Neo4j 知识图谱任务")
async def task_sync_neo4j(
    request: Request, background_tasks: BackgroundTasks
) -> JSONResponse:
    """手动触发同步 MySQL 到 Neo4j 知识图谱任务接口"""

    background_tasks.add_task(sync_mysql_to_neo4j_async)
    return success()
