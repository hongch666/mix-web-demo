from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from app.core import Constants, logger
from app.db import create_tables, get_db, load_config, start_nacos
from app.services import AnalyzeService, start_scheduler

from fastapi import FastAPI

server_config = load_config("server")
IP = server_config["ip"]
PORT = server_config["port"]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    create_tables(["ai_history"])
    start_nacos(ip=IP, port=PORT)
    logger.info("Nacos 服务注册成功")
    analyze_service = AnalyzeService.create_for_scheduler()
    start_scheduler(analyze_service=analyze_service, db_factory=lambda: next(get_db()))
    logger.info(Constants.STARTUP_MESSAGE)
    logger.info(f"服务地址:http://{IP}:{PORT}")
    logger.info(f"Swagger文档地址: http://{IP}:{PORT}/docs")
    logger.info(f"ReDoc文档地址: http://{IP}:{PORT}/redoc")
    yield
