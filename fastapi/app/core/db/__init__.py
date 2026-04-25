from typing import Any, List, NoReturn

from app.core.base import Constants, Logger

try:
    from app.core.config import (
        get_service_instance,
        register_instance,
        start_nacos,
    )
except Exception as _exc:
    _nacos_error: str = str(_exc)
    Logger.error(f"导入 Nacos 相关函数时出错: {_nacos_error}")

    def _missing_nacos(*args: Any, **kwargs: Any) -> NoReturn:
        raise RuntimeError(Constants.NACOS_INITIALIZATION_FAILED)

    get_service_instance = _missing_nacos
    register_instance = _missing_nacos
    start_nacos = _missing_nacos

from .mongodb import async_client, async_db
from .mysql import (
    AsyncSessionLocal,
    Base,
    SessionLocal,
    async_engine,
    create_tables_async,
    engine,
    get_db,
    get_db_async,
)

try:
    from .clickhouse import ClickhouseConnectionPool, get_clickhouse_connection_pool
except ModuleNotFoundError as _exc:
    _clickhouse_error: str = str(_exc)
    Logger.error(f"导入 ClickhouseConnectionPool 时出错: {_clickhouse_error}")

    class ClickhouseConnectionPool:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ModuleNotFoundError("clickhouse-driver 未安装")

    def get_clickhouse_connection_pool(*args: Any, **kwargs: Any) -> NoReturn:
        raise ModuleNotFoundError("clickhouse-driver 未安装")


try:
    from .rabbitmq import (
        RabbitMQClient,
        _rabbitmq_client,
        get_rabbitmq_client,
        send_to_queue_async,
    )
except ModuleNotFoundError as _exc:
    _rabbitmq_error: str = str(_exc)
    Logger.error(f"导入 RabbitMQClient 时出错: {_rabbitmq_error}")

    class RabbitMQClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ModuleNotFoundError(Constants.AIO_PKA_NOT_INSTALLED_ERROR)

    _rabbitmq_client = None

    def get_rabbitmq_client(*args: Any, **kwargs: Any) -> NoReturn:
        raise ModuleNotFoundError(Constants.AIO_PKA_NOT_INSTALLED_ERROR)

    def send_to_queue_async(*args: Any, **kwargs: Any) -> NoReturn:
        raise ModuleNotFoundError(Constants.AIO_PKA_NOT_INSTALLED_ERROR)


try:
    from .redis import RedisClient, get_redis_client
except ModuleNotFoundError as _exc:
    _redis_error: str = str(_exc)
    Logger.error(f"导入 RedisClient 时出错: {_redis_error}")

    class RedisClient:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ModuleNotFoundError(Constants.REDIS_NOT_INSTALLED_ERROR)

    def get_redis_client(*args: Any, **kwargs: Any) -> NoReturn:
        raise ModuleNotFoundError(Constants.REDIS_NOT_INSTALLED_ERROR)


__all__: List[str] = [
    "async_client",
    "async_db",
    "get_db",
    "get_db_async",
    "create_tables_async",
    "engine",
    "async_engine",
    "Base",
    "AsyncSessionLocal",
    "SessionLocal",
    "start_nacos",
    "register_instance",
    "get_service_instance",
    "RabbitMQClient",
    "get_rabbitmq_client",
    "send_to_queue_async",
    "_rabbitmq_client",
    "ClickhouseConnectionPool",
    "get_clickhouse_connection_pool",
    "RedisClient",
    "get_redis_client",
]
