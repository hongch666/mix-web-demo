from app.core.config.config import load_config

try:
    from app.core.config.nacos import (
        get_service_instance,
        register_instance,
        start_nacos,
    )
except Exception:

    def _missing_nacos(*args, **kwargs):
        raise RuntimeError(f"nacos 初始化不可用: {exc}") from exc

    get_service_instance = _missing_nacos
    register_instance = _missing_nacos
    start_nacos = _missing_nacos

from .mongodb import client, db
from .mysql import create_tables, get_db

try:
    from .hive import HiveConnectionPool, get_hive_connection_pool
except ModuleNotFoundError:

    class HiveConnectionPool:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError(
                "pyhive 未安装，请先执行 `uv sync` 或安装 `pyhive`。"
            ) from exc

    def get_hive_connection_pool(*args, **kwargs):  # type: ignore[no-redef]
        raise ModuleNotFoundError(
            "pyhive 未安装，请先执行 `uv sync` 或安装 `pyhive`。"
        ) from exc


try:
    from .oss import OSSClient
except ModuleNotFoundError:

    class OSSClient:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError(
                "oss2 未安装，请先执行 `uv sync` 或安装 `oss2`。"
            ) from exc


try:
    from .rabbitmq import (
        RabbitMQClient,
        _rabbitmq_client,
        get_rabbitmq_client,
        send_to_queue,
    )
except ModuleNotFoundError:

    class RabbitMQClient:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError(
                "pika 未安装，请先执行 `uv sync` 或安装 `pika`。"
            ) from exc

    _rabbitmq_client = None  # type: ignore[assignment]

    def get_rabbitmq_client(*args, **kwargs):  # type: ignore[no-redef]
        raise ModuleNotFoundError(
            "pika 未安装，请先执行 `uv sync` 或安装 `pika`。"
        ) from exc

    def send_to_queue(*args, **kwargs):  # type: ignore[no-redef]
        raise ModuleNotFoundError(
            "pika 未安装，请先执行 `uv sync` 或安装 `pika`。"
        ) from exc


try:
    from .redis import RedisClient, get_redis_client
except ModuleNotFoundError:

    class RedisClient:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError(
                "redis 未安装，请先执行 `uv sync` 或安装 `redis`。"
            ) from exc

    def get_redis_client(*args, **kwargs):  # type: ignore[no-redef]
        raise ModuleNotFoundError(
            "redis 未安装，请先执行 `uv sync` 或安装 `redis`。"
        ) from exc


__all__ = [
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
