from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Optional

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base import Logger
from app.core.client import set_shared_http_client, start_nacos
from app.core.config import load_config
from app.core.constants import Messages
from app.core.grpc import GrpcServerManager
from app.core.grpc.server import create_grpc_server_manager
from app.core.db import (
    AsyncSessionLocal,
    RabbitMQClient,
    async_engine,
    create_tables_async,
    get_clickhouse_connection_pool,
    get_neo4j_client,
    get_rabbitmq_client,
)
from app.internal.agents.langsmith import (
    init_langsmith,
    load_langsmith_config,
    shutdown_langsmith,
)
from app.internal.clients import NestjsClient, SpringClient
from app.internal.models import AiHistory
from app.internal.services import AnalyzeService
from app.internal.tasks import start_scheduler

# 加载服务器配置
server_config: dict[str, Any] = load_config("server")
IP: str = Messages.INIT_IP
PORT: int = server_config["port"]

# 导入并保留实体引用，确保模型已注册到 Base.metadata
SQLALCHEMY_MODELS: tuple[type[AiHistory], ...] = (AiHistory,)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    scheduler: Optional[AsyncIOScheduler] = None
    grpc_server: GrpcServerManager = create_grpc_server_manager()
    # LangSmith 初始化（追踪关闭或失败时均不阻断业务启动）
    langsmith_config = load_langsmith_config()
    init_langsmith(langsmith_config)

    await create_tables_async()
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

    scheduler = start_scheduler(
        analyze_service=analyze_service,
        db_factory=db_factory,
        nestjs_client=NestjsClient(),
        spring_client=SpringClient(),
    )

    # 初始化跨服务调用的 httpx 长连接池（复用连接，降低延迟）
    remote_call_config: dict[str, Any] = load_config("remote_call")
    default_timeout: float = float(remote_call_config["timeout"])
    shared_http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(default_timeout, connect=min(5.0, default_timeout)),
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
    )
    set_shared_http_client(shared_http_client)
    Logger.info(Messages.HTTP_CLIENT_POOL_INITIALIZED)
    await grpc_server.start()

    Logger.info(Messages.STARTUP_MESSAGE)
    Logger.info(Messages.STARTUP_SERVICE_ADDRESS(IP, PORT))
    Logger.info(Messages.STARTUP_SWAGGER_ADDRESS(IP, PORT))
    Logger.info(Messages.STARTUP_REDOC_ADDRESS(IP, PORT))

    yield

    if scheduler:
        scheduler.shutdown(wait=False)
        Logger.info(Messages.SCHEDULER_STOPPED)

    await grpc_server.stop()

    await get_neo4j_client().close()
    await get_clickhouse_connection_pool().close_all_async()
    await async_engine.dispose()

    # 应用关闭时清理 httpx 连接池
    await shared_http_client.aclose()
    Logger.info(Messages.HTTP_CLIENT_POOL_CLOSED)

    # 应用关闭时清理 RabbitMQ 连接
    if rabbitmq_client:
        await rabbitmq_client.close_async()
        Logger.info(Messages.RABBITMQ_CONNECTION_CLOSED_MESSAGE)

    # LangSmith 关闭（flush 缓冲区）
    shutdown_langsmith()
