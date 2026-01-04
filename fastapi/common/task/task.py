from functools import partial
from typing import Optional, Callable, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import BaseScheduler
from sqlmodel import Session
from common.utils import fileLogger as logger
from .hiveSyncTask import export_articles_to_csv_and_hive
from .vectorSyncTask import export_article_vectors_to_postgres

def start_scheduler(
    article_mapper: Optional[Any] = None,
    user_mapper: Optional[Any] = None,
    db_factory: Optional[Callable[[], Session]] = None,
    mysql_db_factory: Optional[Callable[[], Session]] = None,
) -> BaseScheduler:
    """
    启动调度器，可把依赖注入进来（用于测试或容器式管理）。
    例如：
      start_scheduler(
          article_mapper=get_article_mapper(), 
          db_factory=lambda: next(get_db())
      )
    """
    scheduler: BackgroundScheduler = BackgroundScheduler()

    # 任务1：导出文章到 CSV 和 Hive
    export_job_func = partial(
        export_articles_to_csv_and_hive, 
        article_mapper=article_mapper, 
        user_mapper=user_mapper, 
        db_factory=db_factory or mysql_db_factory
    )
    # 每1天执行一次
    scheduler.add_job(export_job_func, 'interval', hours=24, id='export_articles')
    
    # 任务2：同步文章向量到 PostgreSQL（使用LangChain）- 增量同步模式
    sync_vector_job_func = partial(
        export_article_vectors_to_postgres,
        article_mapper=article_mapper,
        mysql_db_factory=mysql_db_factory or db_factory,
        enable_incremental_sync=True  # 启用增量同步
    )
    # 每1天执行一次
    scheduler.add_job(sync_vector_job_func, 'interval', hours=24, id='sync_vectors')
    
    scheduler.start()
    logger.info("定时任务调度器已启动：")
    logger.info("  - 文章导出任务：每 1 天执行一次（包含缓存清理）")
    logger.info("  - 向量同步任务：每 1 天执行一次")
    return scheduler