from typing import Any, List, NoReturn

from app.core import load_config

try:
    from app.core import (
        get_service_instance,
        register_instance,
        start_nacos,
    )
except Exception as _exc:
    _nacos_error: str = str(_exc)

    def _missing_nacos(*args: Any, **kwargs: Any) -> NoReturn:
        raise RuntimeError(f"nacos 初始化不可用: {_nacos_error}")

    get_service_instance = _missing_nacos
    register_instance = _missing_nacos
    start_nacos = _missing_nacos

from .mongodb import client, db
from .mysql import create_tables, get_db

try:
    from .hive import HiveConnectionPool, get_hive_connection_pool
except ModuleNotFoundError as _exc:
    _hive_error: str = str(_exc)

    class HiveConnectionPool:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ModuleNotFoundError(
                "pyhive 未安装，请先执行 `uv sync` 或安装 `pyhive`。"
            )

    def get_hive_connection_pool(*args: Any, **kwargs: Any) -> NoReturn:
        raise ModuleNotFoundError("pyhive 未安装，请先执行 `uv sync` 或安装 `pyhive`。")


try:
    from .oss import OSSClient
except ModuleNotFoundError as _exc:
    _oss_error: str = str(_exc)

    class OSSClient:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ModuleNotFoundError("oss2 未安装，请先执行 `uv sync` 或安装 `oss2`。")


try:
    from .rabbitmq import (
        RabbitMQClient,
        _rabbitmq_client,
        get_rabbitmq_client,
        send_to_queue,
    )
except ModuleNotFoundError as _exc:
    _rabbitmq_error: str = str(_exc)

    class RabbitMQClient:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ModuleNotFoundError("pika 未安装，请先执行 `uv sync` 或安装 `pika`。")

    _rabbitmq_client = None  # type: ignore[assignment]

    def get_rabbitmq_client(*args: Any, **kwargs: Any) -> NoReturn:  # type: ignore[no-redef]
        raise ModuleNotFoundError("pika 未安装，请先执行 `uv sync` 或安装 `pika`。")

    def send_to_queue(*args: Any, **kwargs: Any) -> NoReturn:  # type: ignore[no-redef]
        raise ModuleNotFoundError("pika 未安装，请先执行 `uv sync` 或安装 `pika`。")


try:
    from .redis import RedisClient, get_redis_client
except ModuleNotFoundError as _exc:
    _redis_error: str = str(_exc)

    class RedisClient:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ModuleNotFoundError(
                "redis 未安装，请先执行 `uv sync` 或安装 `redis`。"
            )

    def get_redis_client(*args: Any, **kwargs: Any) -> NoReturn:  # type: ignore[no-redef]
        raise ModuleNotFoundError("redis 未安装，请先执行 `uv sync` 或安装 `redis`。")


__all__: List[str] = [
    "load_config",
    "client",
    "db",
    "get_db",
    "create_tables",
    "start_nacos",
    "register_instance",
    "get_service_instance",
    "OSSClient",
    "RabbitMQClient",
    "get_rabbitmq_client",
    "send_to_queue",
    "_rabbitmq_client",
    "HiveConnectionPool",
    "get_hive_connection_pool",
    "RedisClient",
    "get_redis_client",
]
