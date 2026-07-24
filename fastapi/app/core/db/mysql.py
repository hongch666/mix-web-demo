import traceback
from collections.abc import AsyncGenerator
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from app.core.base import Logger
from app.core.config import load_config
from app.core.constants import Messages
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session as SASession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

Base = declarative_base()

server_config: Dict[str, Any] = load_config("server")
mysql_config: Dict[str, Any] = load_config("database")["mysql"]
SERVER_MODE: str = str(server_config.get("mode", "dev")).strip().lower()
HOST: str = mysql_config["host"]
PORT: int = mysql_config["port"]
DATABASE: str = mysql_config["database"]
USER: str = mysql_config["user"]
PASSWORD: str = str(mysql_config["password"])
ENCODED_PASSWORD: str = quote_plus(str(PASSWORD))

DATABASE_URL: str = f"mysql+pymysql://{USER}:{ENCODED_PASSWORD}@{HOST}:{PORT}/{DATABASE}?charset=utf8mb4"
ASYNC_DATABASE_URL: str = f"mysql+aiomysql://{USER}:{ENCODED_PASSWORD}@{HOST}:{PORT}/{DATABASE}?charset=utf8mb4"

POOL_SIZE: int = int(mysql_config.get("pool_size", 30))
MAX_OVERFLOW: int = int(mysql_config.get("max_overflow", 80))
POOL_RECYCLE: int = int(mysql_config.get("pool_recycle", 3600))
POOL_PRE_PING: bool = mysql_config.get("pool_pre_ping", True)
POOL_TIMEOUT: int = int(mysql_config.get("pool_timeout", 30))
READ_TIMEOUT: int = int(mysql_config.get("read_timeout", 120))
WRITE_TIMEOUT: int = int(mysql_config.get("write_timeout", 120))
AUTOCOMMIT: bool = mysql_config.get("autocommit", False)
ECHO: bool = SERVER_MODE == "dev"

# 配置连接池参数以支持高并发访问
engine: Engine = create_engine(
    DATABASE_URL,
    echo=ECHO,
    poolclass=QueuePool,
    pool_size=POOL_SIZE,  # 基础连接池大小
    max_overflow=MAX_OVERFLOW,  # 最多额外创建的连接数
    pool_recycle=POOL_RECYCLE,  # 连接回收时间（秒）
    pool_pre_ping=POOL_PRE_PING,  # 每次取连接前进行ping检查
    pool_timeout=POOL_TIMEOUT,  # 获取连接的超时时间（秒）
    connect_args={
        "read_timeout": READ_TIMEOUT,  # pymysql 读超时（秒）
        "write_timeout": WRITE_TIMEOUT,  # pymysql 写超时（秒）
        "autocommit": AUTOCOMMIT,
    },
)

async_engine: AsyncEngine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=ECHO,
    pool_pre_ping=POOL_PRE_PING,
    pool_recycle=POOL_RECYCLE,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    connect_args={
        "autocommit": AUTOCOMMIT,
    },
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
    class_=SASession,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库异步会话（aiomysql 驱动，不阻塞 asyncio 事件循环）

    使用 AsyncSessionLocal + aiomysql 异步驱动，所有数据库操作均通过
    await 执行，完全释放 asyncio 事件循环。
    """
    async with AsyncSessionLocal() as session:
        yield session


async def get_db_sync() -> AsyncGenerator[SASession, None]:
    """获取数据库同步会话（通过线程池桥接，避免阻塞 asyncio 事件循环）

    使用 pymysql 同步驱动，通过 run_in_threadpool 将 session 的
    创建和关闭操作放到独立线程池执行。

    建议逐步迁移到 get_db()（AsyncSession + aiomysql）以获得最佳性能。
    """
    session: SASession = await run_in_threadpool(SessionLocal)
    try:
        yield session
    finally:
        await run_in_threadpool(session.close)


async def create_tables_async(tables: Optional[List[str]] = None) -> None:
    """
    使用异步 MySQL 连接创建数据库表。

    Args:
        tables: 要创建的表名列表，如 ['ai_history']
    """

    try:
        if tables and "ai_history" in tables:
            async with async_engine.begin() as connection:
                result = await connection.exec_driver_sql(
                    Messages.AI_CHAT_SQL_TABLE_EXISTENCE_CHECK,
                    (DATABASE,),
                )
                table_exists: bool = result.fetchone() is not None

                if not table_exists:
                    await connection.exec_driver_sql(
                        Messages.AI_CHAT_SQL_TABLE_CREATION_MESSAGE
                    )
                    Logger.info(Messages.AI_CHAT_TABLE_CREATION_MESSAGE)
                else:
                    Logger.info(Messages.AI_CHAT_TABLE_EXISTS_MESSAGE)
        else:
            Logger.warning(Messages.AI_CHAT_TABLE_UNSUPPORTED_MESSAGE)
    except Exception as e:
        Logger.error(Messages.DATABASE_TABLE_CREATION_FAILED(e))
        Logger.error(traceback.format_exc())
