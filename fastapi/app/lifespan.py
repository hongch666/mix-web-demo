from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.base import Constants, Logger
from app.core.client import start_nacos, set_shared_http_client
from app.core.config import load_config
from app.core.db import RabbitMQClient, SessionLocal, create_tables_async, get_rabbitmq_client
from app.internal.services import AnalyzeService
from app.internal.tasks import start_scheduler
from fastapi import FastAPI

# 加载服务器配置
server_config: Dict[str, Any] = load_config("server")
IP: str = Constants.INIT_IP
PORT: int = server_config["port"]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    await create_tables_async(["ai_history"])
    start_nacos(ip=IP, port=PORT)
    Logger.info(Constants.NACOS_REGISTER_SUCCESS)

    # 初始化 RabbitMQ 连接（RobustConnection 后续自动处理重连）
    rabbitmq_client: Optional[RabbitMQClient] = get_rabbitmq_client()
    if rabbitmq_client:
        await rabbitmq_client.connect()
    else:
        Logger.warning(Constants.RABBITMQ_CLIENT_NOT_INITIALIZED_MESSAGE)

    analyze_service: AnalyzeService = AnalyzeService.create_for_scheduler()

    def db_factory() -> Session:
        return SessionLocal()

    start_scheduler(analyze_service=analyze_service, db_factory=db_factory)

    # 初始化跨服务调用的 httpx 长连接池（复用连接，降低延迟）
    shared_http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=5.0),
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
    )
    set_shared_http_client(shared_http_client)
    Logger.info(Constants.HTTP_CLIENT_POOL_INITIALIZED)

    Logger.info(Constants.STARTUP_MESSAGE)
    Logger.info(f"服务地址:http://{IP}:{PORT}")
    Logger.info(f"Swagger文档地址: http://{IP}:{PORT}/docs")
    Logger.info(f"ReDoc文档地址: http://{IP}:{PORT}/redoc")

    yield

    # 应用关闭时清理 httpx 连接池
    await shared_http_client.aclose()
    Logger.info(Constants.HTTP_CLIENT_POOL_CLOSED)

    # 应用关闭时清理 RabbitMQ 连接
    if rabbitmq_client:
        await rabbitmq_client.close_async()
        Logger.info(Constants.RABBITMQ_CONNECTION_CLOSED_MESSAGE)
