from datetime import datetime
from functools import partial
from typing import Any, Callable, Optional

from app.core.base import Constants, Logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.base import BaseScheduler
from sqlalchemy.orm import Session

from .tasks.analyzeCacheTask import update_analyze_caches_async
from .tasks.vectorSyncTask import export_article_vectors_to_postgres_async


def start_scheduler(
    article_mapper: Optional[Any] = None,
    user_mapper: Optional[Any] = None,
    db_factory: Optional[Callable[[], Session]] = None,
    mysql_db_factory: Optional[Callable[[], Session]] = None,
    analyze_service: Optional[Any] = None,
) -> BaseScheduler:
    """
    启动调度器，可把依赖注入进来（用于测试或容器式管理）。
    例如：
      start_scheduler(
          article_mapper=get_article_mapper(),
                    db_factory=lambda: SessionLocal()
      )
    """
    scheduler: AsyncIOScheduler = AsyncIOScheduler()

    # 任务1：同步文章向量到 PostgreSQL（使用LangChain）- 增量同步模式
    sync_vector_job_func = partial(
        export_article_vectors_to_postgres_async,
        article_mapper=article_mapper,
        mysql_db_factory=mysql_db_factory or db_factory,
        enable_incremental_sync=True,  # 启用增量同步
    )
    # 每1天执行一次
    scheduler.add_job(sync_vector_job_func, "interval", hours=24, id="sync_vectors")

    # 任务2：更新分析接口缓存
    analyze_cache_job_func = partial(
        update_analyze_caches_async,
        analyze_service=analyze_service,
        db_factory=db_factory or mysql_db_factory,
    )
    # 每10分钟执行一次，启动时立即执行一次
    scheduler.add_job(
        analyze_cache_job_func,
        "interval",
        minutes=10,
        id="update_analyze_caches",
        next_run_time=datetime.now(),  # 立即执行
    )

    scheduler.start()
    Logger.info(Constants.SCHEDULER_STARTED_MESSAGE)
    Logger.info(Constants.SCHEDULER_VECTOR_SYNC_MESSAGE)
    Logger.info(Constants.SCHEDULER_ANALYZE_CACHE_UPDATE_MESSAGE)
    return scheduler
