import asyncio
import time
from collections.abc import AsyncGenerator
from threading import Condition, Lock
from typing import Any, Optional
from urllib.parse import quote_plus

from clickhouse_driver import Client
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.base import Logger
from app.core.config import load_config
from app.core.constants import Messages

ClickHouseBase = declarative_base()

_server_config: dict[str, Any] = load_config("server")
_clickhouse_config: dict[str, Any] = load_config("database")["clickhouse"]
_host: str = str(_clickhouse_config["host"])
_port: int = int(_clickhouse_config["port"])
_database: str = str(_clickhouse_config["database"])
_username: str = str(_clickhouse_config.get("username", "default"))
_password: str = str(_clickhouse_config.get("password", "") or "")
_encoded_username: str = quote_plus(_username)
_encoded_password: str = quote_plus(_password)

# clickhouse-sqlalchemy 的 asynch 驱动实现了 SQLAlchemy asyncio 适配器。
CLICKHOUSE_ASYNC_DATABASE_URL: str = (
    f"clickhouse+asynch://{_encoded_username}:{_encoded_password}"
    f"@{_host}:{_port}/{_database}"
)
_echo_value: Any = _clickhouse_config.get("echo")
CLICKHOUSE_ECHO: bool = (
    bool(_echo_value)
    if _echo_value is not None
    else str(_server_config.get("mode", "dev")).strip().lower() == "dev"
)
CLICKHOUSE_POOL_SIZE: int = int(_clickhouse_config.get("pool_size", 10))
CLICKHOUSE_MAX_OVERFLOW: int = int(_clickhouse_config.get("max_overflow", 20))
CLICKHOUSE_POOL_RECYCLE: int = int(_clickhouse_config.get("pool_recycle", 3600))
CLICKHOUSE_POOL_TIMEOUT: int = int(_clickhouse_config.get("pool_timeout", 30))
CLICKHOUSE_POOL_PRE_PING: bool = bool(_clickhouse_config.get("pool_pre_ping", True))

clickhouse_async_engine: AsyncEngine = create_async_engine(
    CLICKHOUSE_ASYNC_DATABASE_URL,
    echo=CLICKHOUSE_ECHO,
    pool_pre_ping=CLICKHOUSE_POOL_PRE_PING,
    pool_recycle=CLICKHOUSE_POOL_RECYCLE,
    pool_size=CLICKHOUSE_POOL_SIZE,
    max_overflow=CLICKHOUSE_MAX_OVERFLOW,
    pool_timeout=CLICKHOUSE_POOL_TIMEOUT,
)
ClickHouseAsyncSessionLocal = async_sessionmaker(
    bind=clickhouse_async_engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_clickhouse_db() -> AsyncGenerator[AsyncSession, None]:
    """获取 ClickHouse ORM 异步会话"""

    async with ClickHouseAsyncSessionLocal() as session:
        yield session


async def dispose_clickhouse_async_engine() -> None:
    """释放 ClickHouse ORM 连接池"""

    await clickhouse_async_engine.dispose()


async def create_warehouse_tables_async() -> None:
    """根据数仓 ORM 元数据创建缺失的 ClickHouse 表。"""

    from app.core.base import Logger
    from app.core.constants import Messages
    from app.internal.models import (  # noqa: F401
        AdsApiAverageSpeed,
        AdsApiCalledCount,
        AdsCategoryStats,
        AdsMonthlyPublish,
        AdsPlatformStats,
        AdsSearchKeyword,
        AdsTop10Article,
        AdsUserDay,
        AdsUserStats,
        AdsUserViewArticle,
        DimCategory,
        DimUser,
        DwdApiCall,
        DwdArticleEvent,
        DwdUserAction,
        DwsApiDay,
        DwsArticleDay,
        DwsUserDay,
        OdsApiLog,
        OdsArticle,
        OdsArticleLog,
        OdsCategory,
        OdsCollect,
        OdsComment,
        OdsFocus,
        OdsLike,
        OdsSubCategory,
        OdsUser,
        SyncWatermark,
    )
    from app.internal.models.warehouse.base import configure_warehouse_engines

    try:
        configure_warehouse_engines(ClickHouseBase.metadata)
        # ClickHouse 不支持事务提交，DDL 通过独立连接执行即可。
        async with clickhouse_async_engine.connect() as connection:
            await connection.run_sync(ClickHouseBase.metadata.create_all)
        Logger.info(Messages.WAREHOUSE_SCHEMA_READY)
    except Exception as error:
        Logger.error(Messages.WAREHOUSE_SCHEMA_CREATION_FAILED(error))


# 与项目现有 Clickhouse 命名风格保持兼容。
ClickhouseBase = ClickHouseBase
ClickhouseAsyncSessionLocal = ClickHouseAsyncSessionLocal


class ClickhouseConnectionPool:
    """ClickHouse 连接池 - 单例模式"""

    _instance: Optional["ClickhouseConnectionPool"] = None
    _connections: list[Any] = []
    _max_connections: int = 10
    _conn_count: int = 0  # 统计创建的连接数
    _active_connections: int = 0
    _lock: Lock
    _condition: Condition

    def __new__(cls) -> "ClickhouseConnectionPool":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._lock = Lock()
            cls._instance._condition = Condition(cls._instance._lock)
        return cls._instance

    def get_connection(self) -> Any:
        """从池中获取连接"""
        with self._condition:
            if self._connections:
                conn: Any = self._connections.pop()
                Logger.info(Messages.CLICKHOUSE_POOL_REUSED(len(self._connections)))
                return conn

            if self._active_connections < self._max_connections:
                self._active_connections += 1
                self._conn_count += 1
                conn_index: int = self._conn_count
            else:
                Logger.warning(
                    Messages.CLICKHOUSE_POOL_EXHAUSTED(
                        self._active_connections, self._max_connections
                    )
                )
                while not self._connections:
                    self._condition.wait()
                conn: Any = self._connections.pop()
                Logger.info(
                    Messages.CLICKHOUSE_POOL_REUSED_AFTER_WAIT(len(self._connections))
                )
                return conn

        # 如果池为空，创建新连接
        clickhouse_config: dict[str, Any] = load_config("database")["clickhouse"]
        ch_host: str = str(clickhouse_config["host"])
        ch_port: int = int(clickhouse_config["port"])
        ch_database: str = str(clickhouse_config["database"])
        ch_username: str = str(clickhouse_config["username"])
        # 确保密码始终是字符串类型
        ch_password: str = str(clickhouse_config["password"])
        if not ch_password or ch_password == "None":
            ch_password = ""

        Logger.info(Messages.CLICKHOUSE_CONNECTION_CREATING(conn_index))
        Logger.info(
            Messages.CLICKHOUSE_CONNECTION_CONFIG(
                ch_host, ch_port, ch_database, ch_username
            )
        )
        conn_start: float = time.time()

        try:
            conn: Any = Client(
                host=ch_host,
                port=ch_port,
                database=ch_database,
                user=ch_username,
                password=ch_password,
                settings={"use_numpy": False},
                client_name="fastapi-app",
            )
            conn_time: float = time.time() - conn_start
            Logger.info(Messages.CLICKHOUSE_CONNECTION_CREATED(conn_time))
            return conn
        except Exception as e:
            with self._condition:
                self._active_connections = max(self._active_connections - 1, 0)
                self._condition.notify()
            Logger.error(Messages.CLICKHOUSE_CONNECTION_CREATE_FAILED(e))
            raise

    def return_connection(self, conn: Any) -> None:
        """归还连接到池"""
        if conn is None:
            return

        with self._condition:
            if len(self._connections) < self._max_connections:
                self._connections.append(conn)
                Logger.info(
                    Messages.CLICKHOUSE_CONNECTION_RETURNED(len(self._connections))
                )
                self._condition.notify()
                return

            self._active_connections = max(self._active_connections - 1, 0)
            self._condition.notify()

        try:
            conn.disconnect()
        except Exception:
            pass
        Logger.info(Messages.CLICKHOUSE_CONNECTION_POOL_FULL_MESSAGE)

    def close_all(self) -> None:
        """关闭所有连接"""
        for conn in self._connections:
            try:
                conn.disconnect()
            except Exception:
                pass
        self._connections.clear()
        self._active_connections = 0
        Logger.info(Messages.CLICKHOUSE_CONNECTION_POOL_CLOSED_MESSAGE)

    async def get_connection_async(self) -> Any:
        return await asyncio.to_thread(self.get_connection)

    async def return_connection_async(self, conn: Any) -> None:
        await asyncio.to_thread(self.return_connection, conn)

    async def close_all_async(self) -> None:
        await asyncio.to_thread(self.close_all)


# 全局单例
_clickhouse_pool: Optional[ClickhouseConnectionPool] = None


def get_clickhouse_connection_pool() -> ClickhouseConnectionPool:
    """获取ClickHouse连接池单例"""
    global _clickhouse_pool
    if _clickhouse_pool is None:
        _clickhouse_pool = ClickhouseConnectionPool()
    return _clickhouse_pool
