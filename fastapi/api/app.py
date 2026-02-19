from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict

from common.config import create_tables, get_db, load_config, start_nacos
from common.handler import exception_handlers
from common.middleware import middlewares
from common.task import start_scheduler
from common.utils import Constants, logger

from api.controller import routers
from api.service import AnalyzeService
from fastapi import FastAPI

server_config: Dict[str, Any] = load_config("server")
IP: str = server_config["ip"]
PORT: int = server_config["port"]


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
        # 自动建表
        create_tables(["ai_history"])
        # 启动Nacos服务注册
        start_nacos(ip=IP, port=PORT)
        # 启动定时任务调度器
        analyze_service: AnalyzeService = AnalyzeService.create_for_scheduler()
        start_scheduler(
            analyze_service=analyze_service, db_factory=lambda: next(get_db())
        )
        # 记录启动日志
        logger.info(Constants.STARTUP_MESSAGE)
        logger.info(f"服务地址:http://{IP}:{PORT}")
        logger.info(f"Swagger文档地址: http://{IP}:{PORT}/docs")
        logger.info(f"ReDoc文档地址: http://{IP}:{PORT}/redoc")
        yield

    app = FastAPI(
        title=Constants.SWAGGER_TITLE,
        description=Constants.SWAGGER_DESCRIPTION,
        version=Constants.SWAGGER_VERSION,
        lifespan=lifespan,
    )

    # 添加中间件
    for middleware in middlewares:
        app.add_middleware(middleware)
    # 添加异常处理器
    for exception_class, handler in exception_handlers.items():
        app.add_exception_handler(exception_class, handler)
    # 添加路由
    for router in routers:
        app.include_router(router)

    return app
