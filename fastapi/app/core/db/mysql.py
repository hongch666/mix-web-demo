import traceback
from collections.abc import AsyncGenerator
from typing import Any
from urllib.parse import quote_plus

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.base import Logger
from app.core.config import load_config
from app.core.constants import Messages, MySQLIndexes

Base = declarative_base()

server_config: dict[str, Any] = load_config("server")
mysql_config: dict[str, Any] = load_config("database")["mysql"]
SERVER_MODE: str = str(server_config["mode"]).strip().lower()
HOST: str = mysql_config["host"]
PORT: int = mysql_config["port"]
DATABASE: str = mysql_config["database"]
USER: str = mysql_config["user"]
PASSWORD: str = str(mysql_config["password"])
ENCODED_PASSWORD: str = quote_plus(str(PASSWORD))

ASYNC_DATABASE_URL: str = f"mysql+aiomysql://{USER}:{ENCODED_PASSWORD}@{HOST}:{PORT}/{DATABASE}?charset=utf8mb4"

POOL_SIZE: int = int(mysql_config["pool_size"])
MAX_OVERFLOW: int = int(mysql_config["max_overflow"])
POOL_RECYCLE: int = int(mysql_config["pool_recycle"])
POOL_PRE_PING: bool = mysql_config["pool_pre_ping"]
POOL_TIMEOUT: int = int(mysql_config["pool_timeout"])
AUTOCOMMIT: bool = mysql_config["autocommit"]
# 启动期索引补齐开关：大表手动做 DDL 时可在配置中关闭，避免拖慢启动
ENSURE_INDEXES: bool = bool(mysql_config.get("ensure_indexes", True))
# SQL 日志回显开关：优先使用显式配置，未配置时根据 SERVER_MODE 自动判断
_echo_val = mysql_config.get("echo")
ECHO: bool = _echo_val if _echo_val is not None else SERVER_MODE == "dev"

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

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库异步会话（aiomysql 驱动，不阻塞 asyncio 事件循环）

    使用 AsyncSessionLocal + aiomysql 异步驱动，所有数据库操作均通过
    await 执行，完全释放 asyncio 事件循环
    """
    async with AsyncSessionLocal() as session:
        yield session


async def create_tables_async() -> None:
    """
    根据已注册的 SQLAlchemy 实体创建不存在的数据库表

    SQLAlchemy 的 create_all 只负责创建缺失的表，不会执行已有表的结构迁移
    """

    try:
        async with async_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        Logger.info(Messages.DATABASE_TABLE_INITIALIZATION_SUCCESS)
    except Exception as e:
        Logger.error(Messages.DATABASE_TABLE_CREATION_FAILED(e))
        Logger.error(traceback.format_exc())


async def create_mysql_indexes_async() -> None:
    """为已存在的业务表补齐缺失索引

    MySQL 不支持 CREATE INDEX IF NOT EXISTS，且 create_all 不会修改已存在表的结构，
    所以这里先查 information_schema.statistics，缺失时才执行 ALTER TABLE；
    表不存在时查无记录直接跳过，兼容只启动单个服务的部署方式
    """

    if not ENSURE_INDEXES:
        Logger.info(Messages.MYSQL_INDEX_INITIALIZATION_SUCCESS)
        return

    statement = (
        "SELECT 1 FROM information_schema.statistics "
        "WHERE table_schema = DATABASE() "
        "AND table_name = :table_name "
        "AND index_name = :index_name "
        "LIMIT 1"
    )

    try:
        async with async_engine.begin() as connection:
            for table, index_name, columns in MySQLIndexes.ALL:
                exists = (
                    await connection.execute(
                        text(statement),
                        {"table_name": table, "index_name": index_name},
                    )
                ).first()
                if exists:
                    continue
                await connection.execute(
                    text(f"ALTER TABLE `{table}` ADD INDEX `{index_name}` {columns}")
                )
        Logger.info(Messages.MYSQL_INDEX_INITIALIZATION_SUCCESS)
    except Exception as e:
        Logger.error(Messages.MYSQL_INDEX_INITIALIZATION_FAILED(e))
        Logger.error(traceback.format_exc())
