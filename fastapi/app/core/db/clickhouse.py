from collections.abc import AsyncGenerator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Any, Optional
from urllib.parse import quote_plus

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

# clickhouse-sqlalchemy 的 asynch 驱动实现了 SQLAlchemy asyncio 适配器
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

ClickHouseSessionFactory = Callable[[], AbstractAsyncContextManager[AsyncSession]]


@asynccontextmanager
async def clickhouse_session() -> AsyncGenerator[AsyncSession, None]:
    """ClickHouse ORM 会话上下文管理器

    ClickHouse ORM 访问的唯一入口：请求链路内的数仓 Mapper 与依赖注入
    （get_clickhouse_db）都由此获取会话，保证创建方式与生命周期一致

    注意会话粒度仍是每次查询一个，因为数仓查询存在 asyncio.gather 并发，
    而 AsyncSession 不支持并发复用
    """

    async with ClickHouseAsyncSessionLocal() as session:
        yield session


async def get_clickhouse_db() -> AsyncGenerator[AsyncSession, None]:
    """获取 ClickHouse ORM 异步会话（FastAPI 依赖形式）"""

    async with clickhouse_session() as session:
        yield session


def get_clickhouse_session_factory() -> ClickHouseSessionFactory:
    """返回用于并发 ClickHouse 查询的独立会话工厂"""
    return clickhouse_session


async def dispose_clickhouse_async_engine() -> None:
    """释放 ClickHouse ORM 连接池"""

    await clickhouse_async_engine.dispose()


async def execute_clickhouse_sql(
    sql: str, parameters: Optional[dict[str, Any]] = None
) -> None:
    """通过 SQLAlchemy 异步引擎执行无需返回结果的 ClickHouse SQL"""

    async with clickhouse_async_engine.connect() as connection:
        await connection.exec_driver_sql(sql, parameters or {})


async def execute_clickhouse_query(
    sql: str,
    parameters: Optional[dict[str, Any]] = None,
) -> list[Any]:
    """通过 SQLAlchemy 异步引擎执行 ClickHouse 查询并返回行元组列表"""

    async with clickhouse_async_engine.connect() as connection:
        result = await connection.exec_driver_sql(sql, parameters or {})
        return [tuple(row) for row in result.fetchall()]


async def create_warehouse_tables_async() -> None:
    """根据数仓 ORM 元数据创建缺失的 ClickHouse 表"""

    # 延迟导入避免 app.core.db 与 app.internal.models 循环依赖
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
        configure_warehouse_engines,
    )

    try:
        configure_warehouse_engines(ClickHouseBase.metadata)
        # ClickHouse 不支持事务提交，DDL 通过独立连接执行即可
        async with clickhouse_async_engine.connect() as connection:
            await connection.run_sync(ClickHouseBase.metadata.create_all)
        Logger.info(Messages.WAREHOUSE_SCHEMA_READY)
    except Exception as error:
        Logger.error(Messages.WAREHOUSE_SCHEMA_CREATION_FAILED(error))


# 与项目现有 Clickhouse 命名风格保持兼容
ClickhouseBase = ClickHouseBase
ClickhouseAsyncSessionLocal = ClickHouseAsyncSessionLocal
