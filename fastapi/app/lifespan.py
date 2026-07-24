from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.internal.agents.langsmith import init_langsmith, load_langsmith_config, shutdown_langsmith
from app.core.base import Logger
from app.core.client import set_shared_http_client, start_nacos
from app.core.config import load_config
from app.core.constants import InitMessages, Messages
from app.core.db import (
    AsyncSessionLocal,
    RabbitMQClient,
    create_tables_async,
    get_rabbitmq_client,
)
from app.internal.services import AnalyzeService
from app.internal.tasks import start_scheduler
from fastapi import FastAPI

# 加载服务器配置
server_config: Dict[str, Any] = load_config("server")
IP: str = InitMessages.INIT_IP
PORT: int = server_config["port"]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    # LangSmith 初始化（追踪关闭或失败时均不阻断业务启动）
    langsmith_config = load_langsmith_config()
    init_langsmith(langsmith_config)

    await create_tables_async(["ai_history"])
    start_nacos(ip=IP, port=PORT)
    Logger.info(Messages.NACOS_REGISTER_SUCCESS)

    # 初始化 RabbitMQ 连接（RobustConnection 后续自动处理重连）
    rabbitmq_client: Optional[RabbitMQClient] = get_rabbitmq_client()
    if rabbitmq_client:
        await rabbitmq_client.connect()
    else:
        Logger.warning(Messages.RABBITMQ_CLIENT_NOT_INITIALIZED_MESSAGE)

    analyze_service: AnalyzeService = AnalyzeService.create_for_scheduler()

    def db_factory() -> AsyncSession:
        return AsyncSessionLocal()

    start_scheduler(analyze_service=analyze_service, db_factory=db_factory)

    # 初始化跨服务调用的 httpx 长连接池（复用连接，降低延迟）
    shared_http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=5.0),
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
    )
    set_shared_http_client(shared_http_client)
    Logger.info(InitMessages.HTTP_CLIENT_POOL_INITIALIZED)

    Logger.info(Messages.STARTUP_MESSAGE)
    Logger.info(Messages.STARTUP_SERVICE_ADDRESS(IP, PORT))
    Logger.info(Messages.STARTUP_SWAGGER_ADDRESS(IP, PORT))
    Logger.info(Messages.STARTUP_REDOC_ADDRESS(IP, PORT))

    yield

    # 应用关闭时清理 httpx 连接池
    await shared_http_client.aclose()
    Logger.info(InitMessages.HTTP_CLIENT_POOL_CLOSED)

    # 应用关闭时清理 RabbitMQ 连接
    if rabbitmq_client:
        await rabbitmq_client.close_async()
        Logger.info(Messages.RABBITMQ_CONNECTION_CLOSED_MESSAGE)

    # LangSmith 关闭（flush 缓冲区）
    shutdown_langsmith()
