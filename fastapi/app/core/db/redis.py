import asyncio
import json
import uuid
from datetime import date, datetime
from decimal import Decimal
from threading import Lock
from typing import Any, Optional

import redis.asyncio as redis
from app.core.base import Constants, Logger
from app.core.config import load_config


class RedisClient:
    """Redis 客户端 - 单例模式"""

    _instance: Optional["RedisClient"] = None
    _pool: Optional[Any] = None

    def __new__(cls) -> "RedisClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """加载 Redis 配置，连接池在当前事件循环中按需创建"""
        try:
            self._redis_config = load_config("database")["redis"]
            self._client: Optional[Any] = None
            self._client_loop_id: Optional[int] = None
            self._init_lock = Lock()
        except Exception as e:
            Logger.error(f"{Constants.REDIS_CONNECTION_FAILED_MESSAGE_PREFIX}{e}")
            self._redis_config = None
            self._client = None
            self._client_loop_id = None
            self._init_lock = Lock()

    def _build_pool_params(self) -> dict[str, Any]:
        redis_config = self._redis_config or {}
        pool_params = {
            "host": redis_config.get("host", "127.0.0.1"),
            "port": redis_config.get("port", 6379),
            "db": redis_config.get("db", 0),
            "decode_responses": redis_config.get("decode_responses", True),
            "max_connections": redis_config.get("max_connections", 10),
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
        }
        if redis_config.get("username"):
            pool_params["username"] = redis_config["username"]
        if redis_config.get("password"):
            pool_params["password"] = redis_config["password"]
        return pool_params

    async def _ensure_client(self) -> Optional[Any]:
        """确保当前事件循环对应的 Redis 客户端可用。"""
        if self._redis_config is None:
            return None

        try:
            loop = asyncio.get_running_loop()
            loop_id = id(loop)
        except RuntimeError:
            return self._client

        if self._client is not None and self._client_loop_id == loop_id:
            return self._client

        with self._init_lock:
            if self._client is not None and self._client_loop_id == loop_id:
                return self._client

            pool_params = self._build_pool_params()
            self._pool = redis.ConnectionPool(**pool_params)
            self._client = redis.Redis(connection_pool=self._pool)
            self._client_loop_id = loop_id

            Logger.info(
                f"{Constants.REDIS_CLIENT_INITIALIZED_MESSAGE_PREFIX}{pool_params['host']}:{pool_params['port']}, DB: {pool_params['db']}"
            )
            return self._client

    def get_client(self) -> Optional[Any]:
        """获取 Redis 客户端"""
        return self._client

    def _json_default(self, obj: Any) -> Any:
        """将常见非 JSON 类型转换为可序列化类型"""
        if isinstance(obj, Decimal):
            return int(obj) if obj == obj.to_integral_value() else float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return str(obj)

    async def is_available(self) -> bool:
        """检查 Redis 是否可用"""
        try:
            client = await self._ensure_client()
            if client:
                await client.ping()
                return True
        except Exception:
            pass
        return False

    async def get(self, key: str) -> Optional[Any]:
        """获取值"""
        try:
            client = await self._ensure_client()
            if not client:
                return None
            value = await client.get(key)
            if value:
                try:
                    return json.loads(value)
                except Exception:
                    return value
            return None
        except Exception as e:
            Logger.error(f"{Constants.REDIS_GET_FAILED_MESSAGE_PREFIX}{key}: {e}")
            return None

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """设置值"""
        try:
            client = await self._ensure_client()
            if not client:
                return False
            if isinstance(value, (dict, list)):
                value = json.dumps(
                    value, ensure_ascii=False, default=self._json_default
                )
            await client.set(key, value, ex=ex)
            return True
        except Exception as e:
            Logger.error(f"{Constants.REDIS_SET_FAILED_MESSAGE_PREFIX}{key}: {e}")
            return False

    async def delete(self, *keys: str) -> bool:
        """删除键"""
        try:
            client = await self._ensure_client()
            if not client:
                return False
            await client.delete(*keys)
            return True
        except Exception as e:
            Logger.error(f"{Constants.REDIS_DELETE_FAILED_MESSAGE_PREFIX}{keys}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            client = await self._ensure_client()
            if not client:
                return False
            return (await client.exists(key)) > 0
        except Exception as e:
            Logger.error(f"{Constants.REDIS_EXISTS_FAILED_MESSAGE_PREFIX}{key}: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        try:
            client = await self._ensure_client()
            if not client:
                return False
            return bool(await client.expire(key, seconds))
        except Exception as e:
            Logger.error(f"{Constants.REDIS_EXPIRE_FAILED_MESSAGE_PREFIX}{key}: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """获取剩余生存时间（秒）"""
        try:
            client = await self._ensure_client()
            if not client:
                return -2
            return await client.ttl(key)
        except Exception as e:
            Logger.error(f"{Constants.REDIS_TTL_FAILED_MESSAGE_PREFIX}{key}: {e}")
            return -2

    async def keys(self, pattern: str) -> list[str]:
        """获取匹配的键列表"""
        try:
            client = await self._ensure_client()
            if not client:
                return []
            return await client.keys(pattern)
        except Exception as e:
            Logger.error(f"{Constants.REDIS_KEYS_FAILED_MESSAGE_PREFIX}{pattern}: {e}")
            return []

    async def flushdb(self) -> bool:
        """清空当前数据库"""
        try:
            client = await self._ensure_client()
            if not client:
                return False
            await client.flushdb()
            Logger.warning(Constants.REDIS_DATABASE_CLEARED_MESSAGE)
            return True
        except Exception as e:
            Logger.error(f"{Constants.REDIS_FLUSHDB_FAILED_MESSAGE_PREFIX}{e}")
            return False

    # 分布式锁相关方法

    async def try_lock(self, lock_key: str, expire_seconds: int) -> Optional[str]:
        """
        尝试获取分布式锁，使用 SET NX EX 原子操作

        Args:
            lock_key: 锁的 Redis key
            expire_seconds: 锁的过期时间（秒），应大于任务执行时间，防止死锁

        Returns:
            锁的唯一标识（UUID），获取失败返回 None（Redis 不可用时返回空字符串表示直接执行）
        """
        try:
            client = await self._ensure_client()
            if not client:
                # Redis 未配置，返回空字符串表示单实例模式可直接执行
                return ""
            lock_value = str(uuid.uuid4())
            result = await client.set(lock_key, lock_value, ex=expire_seconds, nx=True)
            return lock_value if result else None
        except Exception as e:
            Logger.error(f"{Constants.REDIS_LOCK_ACQUIRE_ERROR_PREFIX}{lock_key}: {e}")
            return None

    async def unlock(self, lock_key: str, lock_value: str) -> bool:
        """
        释放分布式锁（原子操作，使用 Lua 脚本保证只有锁持有者才能解锁）

        Args:
            lock_key: 锁的 Redis key
            lock_value: 加锁时返回的唯一标识

        Returns:
            是否成功释放
        """
        try:
            client = await self._ensure_client()
            if not client:
                return True
            unlock_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            result = await client.eval(unlock_script, 1, lock_key, lock_value)
            return result == 1
        except Exception as e:
            Logger.error(f"{Constants.REDIS_LOCK_RELEASE_ERROR_PREFIX}{lock_key}: {e}")
            return False


_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """获取 Redis 客户端单例"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client
