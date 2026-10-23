from collections.abc import Callable
from functools import lru_cache
from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.internal.clients import NestjsClient, SpringClient
from app.internal.services.analyze import AnalyzeService
from app.internal.tasks import (
    build_vector_sync_dependencies,
    initialize_article_content_hash_cache_async,
    sync_article_vectors_manually_async,
    sync_neo4j_manually_async,
    sync_warehouse_async,
    update_analyze_caches_manually_async,
)


class TaskService:
    """定时任务手动触发服务，负责把任务逻辑投递到 FastAPI 后台任务执行"""

    def __init__(
        self,
        analyze_service: AnalyzeService,
        db_factory: Callable[[], AsyncSession],
        spring_client: SpringClient,
        nestjs_client: NestjsClient,
    ) -> None:
        """注入分析服务、MySQL 会话工厂与 Spring/NestJS 客户端"""
        self._analyze_service: AnalyzeService = analyze_service
        self._db_factory: Callable[[], AsyncSession] = db_factory
        self._spring_client: SpringClient = spring_client
        self._nestjs_client: NestjsClient = nestjs_client

    def trigger_update_analyze_caches(self, background_tasks: BackgroundTasks) -> None:
        """手动触发更新分析接口缓存任务，投递到后台执行"""
        background_tasks.add_task(
            update_analyze_caches_manually_async,
            self._analyze_service,
            self._db_factory,
        )

    def trigger_vector_sync(
        self, background_tasks: BackgroundTasks, change_type: str, ids: list[int]
    ) -> None:
        """手动触发向量数据库同步任务，投递到后台执行

        携带文章主键时按主键精确同步，否则执行全量增量同步
        """
        background_tasks.add_task(
            sync_article_vectors_manually_async,
            change_type,
            ids,
            build_vector_sync_dependencies(),
        )

    def trigger_init_hash_cache(self, background_tasks: BackgroundTasks) -> None:
        """手动触发初始化文章内容 hash 缓存任务，投递到后台执行"""
        background_tasks.add_task(
            initialize_article_content_hash_cache_async,
            dependencies=build_vector_sync_dependencies(),
        )

    def trigger_clear_analyze_caches(self, background_tasks: BackgroundTasks) -> None:
        """手动触发清除分析相关缓存任务，投递到后台执行"""
        background_tasks.add_task(self._analyze_service.clear_analyze_caches)

    def trigger_neo4j_sync(
        self,
        background_tasks: BackgroundTasks,
        events: list[dict],
        full_sync: bool,
    ) -> None:
        """手动触发同步 MySQL 到 Neo4j 知识图谱任务，投递到后台执行

        携带变更事件时按主键精确同步，否则执行全量或增量同步
        """
        background_tasks.add_task(sync_neo4j_manually_async, events, full_sync)

    def trigger_warehouse_sync(
        self,
        background_tasks: BackgroundTasks,
        resources: Optional[list[str]] = None,
    ) -> None:
        """手动触发 ClickHouse 数仓同步任务，投递到后台执行

        携带资源名时只同步对应源表，否则全表同步
        """
        background_tasks.add_task(
            sync_warehouse_async,
            spring_client=self._spring_client,
            nestjs_client=self._nestjs_client,
            resources=resources,
        )


@lru_cache
def get_task_service(
    analyze_service: AnalyzeService,
    db_factory: Callable[[], AsyncSession],
    spring_client: SpringClient,
    nestjs_client: NestjsClient,
) -> TaskService:
    """获取 TaskService 单例"""
    return TaskService(analyze_service, db_factory, spring_client, nestjs_client)
