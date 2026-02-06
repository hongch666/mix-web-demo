from fastapi import FastAPI
from typing import Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager
from api import controller
from api.service import AnalyzeService
from config import start_nacos, load_config, create_tables, get_db
from common.utils import logger, Constants
from common.middleware import ContextMiddleware
from common.exceptions import BusinessException
from common.handler import global_exception_handler, business_exception_handler
from common.task import start_scheduler

server_config: Dict[str, Any] = load_config("server")
IP: str = server_config["ip"]
PORT: int = server_config["port"]

def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        # 自动建表
        create_tables(['ai_history'])
        # 启动Nacos服务注册
        start_nacos(ip=IP, port=PORT)
        # 启动定时任务调度器
        analyze_service: AnalyzeService = AnalyzeService.create_for_scheduler()
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
        title=Constants.SWAGGER_TITLE,
        description=Constants.SWAGGER_DESCRIPTION,
        version=Constants.SWAGGER_VERSION,
        lifespan=lifespan
    )
    app.add_middleware(ContextMiddleware)
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
    for name in controller.__all__:
        app.include_router(getattr(controller, name))
    return app