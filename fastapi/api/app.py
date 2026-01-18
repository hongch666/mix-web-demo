from fastapi import FastAPI
from typing import Dict, Any
from contextlib import asynccontextmanager
from api import controller
from api.service import AnalyzeService
from api.mapper import (
    get_article_mapper, get_articlelog_mapper, get_user_mapper,
    get_category_mapper, get_like_mapper, get_collect_mapper
)
from common.cache import (
    get_article_cache, get_category_cache, get_publish_time_cache,
    get_statistics_cache, get_wordcloud_cache
)
from config import start_nacos, load_config, create_tables, get_db
from common.utils import logger
from common.middleware import ContextMiddleware
from common.handler import global_exception_handler
from common.task import start_scheduler

server_config: Dict[str, Any] = load_config("server")
IP: str = server_config["ip"]
PORT: int = server_config["port"]

def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # 自动建表
        create_tables(['ai_history'])
        # 启动Nacos服务注册
        start_nacos(ip=IP, port=PORT)
        # 启动定时任务调度器（手动构建 analyze_service 依赖）
        analyze_service = AnalyzeService(
            articleMapper=get_article_mapper(),
            articleLogMapper=get_articlelog_mapper(),
            userMapper=get_user_mapper(),
            categoryMapper=get_category_mapper(),
            likeMapper=get_like_mapper(),
            collectMapper=get_collect_mapper(),
            article_cache=get_article_cache(),
            category_cache=get_category_cache(),
            publish_time_cache=get_publish_time_cache(),
            statistics_cache=get_statistics_cache(),
            wordcloud_cache=get_wordcloud_cache()
        )
        start_scheduler(
            analyze_service=analyze_service,
            db_factory=lambda: next(get_db())
        )
        # 记录启动日志
        logger.info(f"FastAPI应用已启动")
        logger.info(f"服务地址:http://{IP}:{PORT}")
        logger.info(f"Swagger文档地址: http://{IP}:{PORT}/docs")
        logger.info(f"ReDoc文档地址: http://{IP}:{PORT}/redoc")
        yield

    app = FastAPI(
        title="FastAPI部分的Swagger文档集成",
        description="这是demo项目的FastAPI部分的Swagger文档集成",
        version="1.0.0",
        lifespan=lifespan
    )
    app.add_middleware(ContextMiddleware)
    app.add_exception_handler(Exception, global_exception_handler)
    for name in controller.__all__:
        app.include_router(getattr(controller, name))
    return app