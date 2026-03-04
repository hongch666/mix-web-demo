from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Dict

from sqlmodel import Session

from app.core import Constants, logger
from app.db import create_tables, get_db, load_config, start_nacos
from app.services import AnalyzeService, start_scheduler
from fastapi import FastAPI

# 加载服务器配置
server_config: Dict[str, Any] = load_config("server")
IP: str = server_config["ip"]
PORT: int = server_config["port"]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    create_tables(["ai_history"])
    start_nacos(ip=IP, port=PORT)
    logger.info("Nacos 服务注册成功")

    analyze_service: AnalyzeService = AnalyzeService.create_for_scheduler()

    def db_factory() -> Session:
        return next(get_db())

    start_scheduler(analyze_service=analyze_service, db_factory=db_factory)

    logger.info(Constants.STARTUP_MESSAGE)
    logger.info(f"服务地址:http://{IP}:{PORT}")
    logger.info(f"Swagger文档地址: http://{IP}:{PORT}/docs")
    logger.info(f"ReDoc文档地址: http://{IP}:{PORT}/redoc")

    yield
