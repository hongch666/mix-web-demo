import asyncio
import contextlib
import json
import time
from typing import Any, Optional

from app.core.base import Logger, LoggerProtocol
from app.core.constants import Defaults, Messages, RedisKeys
from app.core.db import get_redis_client

from .baseCache import BaseCache

# 广播失效缓存实例注册表：订阅循环收到广播后按命名空间清理对应实例的本地条目
_broadcast_caches: list["KeyedPubSubCache[Any]"] = []

# 失效广播订阅协程，进程内唯一，由 lifespan 启停
_subscriber_task: Optional[asyncio.Task] = None


class KeyedPubSubCache[T](BaseCache[T]):
    """按键分片的两级缓存模板（L1 本地 5 分钟 + L2 Redis 1 天），不使用版本号机制

    失效由同步任务驱动：写入方调用 invalidate_namespace 清空 Redis 中本前缀的全部键，
    并向广播频道发布本缓存的命名空间；各实例的订阅者收到广播后清理自己的本地条目，
    使多实例部署下其它实例的 L1 不会长期持有旧值
    """

    REDIS_KEY_PREFIX: str = ""
    """L2 Redis key 前缀，子类必须覆盖"""

    INVALIDATION_NAMESPACE: str = ""
    """失效广播命名空间，子类必须覆盖，本地条目以该命名空间为前缀存储"""

    L1_MAX_ENTRIES: int = Defaults.L1_CACHE_MAX_ENTRIES
    """L1 本地缓存的最大条目数，子类可按需覆盖"""

    def __init__(self, logger: LoggerProtocol | None = None) -> None:
        """调用父类完成两级缓存依赖初始化，建立本地条目容器并注册到广播清理列表"""
        super().__init__(logger)
        self._local_entries: dict[str, tuple[T, float]] = {}
        register_broadcast_cache(self)

    async def get_entry(self, key: str) -> Optional[T]:
        """按业务键读取缓存，先查本地再查 Redis，L2 命中时回填本地"""
        local_value = self._read_local(key)
        if local_value is not None:
            return local_value

        return await self._read_redis(key)

    async def get(self) -> Optional[T]:
        """按键分片缓存不提供无键读取入口"""
        raise NotImplementedError

    async def set(self, data: T) -> None:
        """按键分片缓存不提供无键写入入口"""
        raise NotImplementedError

    async def set_entry(self, key: str, value: T) -> None:
        """按业务键写入两级缓存"""
        self._write_local(key, value)
        await self._write_redis(key, value)

    async def delete_entry(self, key: str) -> None:
        """按业务键删除两级缓存"""
        self._local_entries.pop(self._local_key(key), None)
        try:
            await self._redis.delete(f"{self.REDIS_KEY_PREFIX}{key}")
        except Exception as e:
            self._logger.error(Messages.CACHE_L2_CLEAR_FAILED(e))

    async def invalidate_namespace(self) -> None:
        """失效本缓存命名空间：清空 Redis 中本前缀的全部键、清理本地条目并发布失效广播"""
        self.clear_local_namespace(self.INVALIDATION_NAMESPACE)

        try:
            keys: list[str] = await self._redis.keys(f"{self.REDIS_KEY_PREFIX}*")
            if keys:
                await self._redis.delete(*keys)
        except Exception as e:
            self._logger.error(Messages.CACHE_L2_CLEAR_FAILED(e))

        await self._publish_invalidation(ids=None, user_ids=None)

    async def invalidate_ids(self, ids: list[int]) -> None:
        """按文章 id 部分失效：清理本地与 Redis 中包含这些 id 段的条目并广播 id 列表

        适用于键中以完整冒号段落携带文章 id 的缓存；Redis 侧按通配模式扫描删除，
        多匹配的键（如 id 为其它键参数的子串）会被顺带删除，仅造成缓存未命中不影响正确性
        """
        await self._publish_and_clear(
            ids=ids,
            user_ids=None,
            clear_local=lambda: self.clear_local_ids(ids),
            delete_store=lambda: self._delete_ids_from_store(ids),
        )

    async def invalidate_user_ids(self, user_ids: list[int]) -> None:
        """按用户 id 部分失效个性化条目：清理本地与 Redis 中以这些用户 id 结尾的条目并广播

        适用于键以用户 id 作为最后一段的个性化缓存；文章维度的键不受影响
        """
        await self._publish_and_clear(
            ids=None,
            user_ids=user_ids,
            clear_local=lambda: self.clear_local_user_ids(user_ids),
            delete_store=lambda: self._delete_user_ids_from_store(user_ids),
        )

    async def _publish_and_clear(
        self,
        ids: Optional[list[int]],
        user_ids: Optional[list[int]],
        clear_local: Any,
        delete_store: Any,
    ) -> None:
        """执行本地与 L2 的部分清理并发布失效广播，广播与清理结果解耦"""
        cleared = clear_local()
        deleted = await delete_store()

        await self._publish_invalidation(ids=ids, user_ids=user_ids)
        self._logger.info(
            Messages.CACHE_PARTIAL_INVALIDATED(
                self.INVALIDATION_NAMESPACE, cleared, deleted
            )
        )

    async def _publish_invalidation(
        self, ids: Optional[list[int]], user_ids: Optional[list[int]]
    ) -> None:
        """向失效广播频道发布命名空间与可选的 id 列表，ids 均为空表示整命名空间失效"""
        payload: dict[str, Any] = {"namespace": self.INVALIDATION_NAMESPACE}
        if ids:
            payload["ids"] = sorted({str(item) for item in ids})
        if user_ids:
            payload["user_ids"] = sorted({str(item) for item in user_ids})

        published = await self._redis.publish(
            RedisKeys.CACHE_INVALIDATE_CHANNEL, json.dumps(payload)
        )
        if not published:
            self._logger.warning(Messages.CACHE_BROADCAST_PUBLISH_FAILED)

    def clear_local_namespace(self, namespace: str) -> int:
        """清理本实例中属于指定命名空间的本地条目，返回清理条数"""
        prefix = f"{namespace}:"
        stale_keys = [key for key in self._local_entries if key.startswith(prefix)]
        for key in stale_keys:
            self._local_entries.pop(key, None)

        if stale_keys:
            self._logger.info(
                Messages.CACHE_BROADCAST_APPLIED(namespace, len(stale_keys))
            )
        return len(stale_keys)

    def clear_local_ids(self, ids: list[int]) -> int:
        """清理本地条目中任一冒号分段命中给定文章 id 的条目，返回清理条数"""
        id_set = {str(item) for item in ids}
        stale_keys = [
            key for key in self._local_entries if id_set & set(key.split(":"))
        ]
        for key in stale_keys:
            self._local_entries.pop(key, None)

        if stale_keys:
            self._logger.info(
                Messages.CACHE_BROADCAST_APPLIED(
                    self.INVALIDATION_NAMESPACE, len(stale_keys)
                )
            )
        return len(stale_keys)

    def clear_local_user_ids(self, user_ids: list[int]) -> int:
        """清理本地条目中最后一段命中给定用户 id 的个性化条目，返回清理条数"""
        user_set = {str(item) for item in user_ids}
        stale_keys = [
            key for key in self._local_entries if key.rsplit(":", 1)[-1] in user_set
        ]
        for key in stale_keys:
            self._local_entries.pop(key, None)

        if stale_keys:
            self._logger.info(
                Messages.CACHE_BROADCAST_APPLIED(
                    self.INVALIDATION_NAMESPACE, len(stale_keys)
                )
            )
        return len(stale_keys)

    async def _delete_ids_from_store(self, ids: list[int]) -> int:
        """从 L2 删除包含给定文章 id 段的键，覆盖「id 为末段」与「id 后还有参数」两种键形"""
        patterns: list[str] = []
        for item in ids:
            patterns.append(f"{self.REDIS_KEY_PREFIX}*:{item}")
            patterns.append(f"{self.REDIS_KEY_PREFIX}*:{item}:*")
        return await self._redis.delete_by_patterns(*patterns)

    async def _delete_user_ids_from_store(self, user_ids: list[int]) -> int:
        """从 L2 删除以给定用户 id 结尾的个性化键"""
        patterns = [f"{self.REDIS_KEY_PREFIX}*:*:{item}" for item in user_ids]
        return await self._redis.delete_by_patterns(*patterns)

    def _local_key(self, key: str) -> str:
        """拼接本地条目 key，以失效命名空间为前缀便于广播清理"""
        return f"{self.INVALIDATION_NAMESPACE}:{key}"

    def _read_local(self, key: str) -> Optional[T]:
        """读取未过期的本地条目，过期条目顺手清理"""
        entry = self._local_entries.get(self._local_key(key))
        if entry is None:
            return None

        value, written_at = entry
        if time.time() - written_at > self._local_cache_ttl:
            self._local_entries.pop(self._local_key(key), None)
            self._logger.info(Messages.L1_CACHE_TTL_EXPIRED)
            return None

        self._logger.info(Messages.CACHE_L1_HIT(time.time() - written_at))
        return value

    def _write_local(self, key: str, value: T) -> None:
        """写入本地条目，超出容量上限时淘汰最早写入的条目"""
        if (
            len(self._local_entries) >= self.L1_MAX_ENTRIES
            and self._local_key(key) not in self._local_entries
        ):
            oldest_key = min(
                self._local_entries, key=lambda item: self._local_entries[item][1]
            )
            self._local_entries.pop(oldest_key, None)

        self._local_entries[self._local_key(key)] = (value, time.time())

    async def _read_redis(self, key: str) -> Optional[T]:
        """读取 L2 缓存，命中时回填本地缓存"""
        try:
            value = await self._redis.get(f"{self.REDIS_KEY_PREFIX}{key}")
            if value is not None:
                self._logger.info(Messages.L2_CACHE_HIT)
                self._write_local(key, value)
                return value

            self._logger.info(Messages.L2_CACHE_MISS)
            return None
        except Exception as e:
            self._logger.error(Messages.CACHE_L2_READ_FAILED(e))
            return None

    async def _write_redis(self, key: str, value: T) -> None:
        """写入 L2 缓存，失败只记录日志"""
        try:
            await self._redis.set(
                f"{self.REDIS_KEY_PREFIX}{key}", value, ex=self._redis_ttl
            )
        except Exception as e:
            self._logger.error(Messages.CACHE_L2_WRITE_FAILED(e))


def register_broadcast_cache(cache: "KeyedPubSubCache[Any]") -> None:
    """把广播失效缓存实例注册进清理列表，重复注册忽略"""
    if cache not in _broadcast_caches:
        _broadcast_caches.append(cache)


def get_broadcast_caches() -> list["KeyedPubSubCache[Any]"]:
    """获取已注册的广播失效缓存实例列表"""
    return list(_broadcast_caches)


async def start_cache_invalidation_subscriber() -> None:
    """启动缓存失效广播订阅协程，重复调用忽略"""
    global _subscriber_task
    if _subscriber_task is not None and not _subscriber_task.done():
        return

    _subscriber_task = asyncio.create_task(_cache_invalidation_loop())


async def stop_cache_invalidation_subscriber() -> None:
    """停止缓存失效广播订阅协程"""
    global _subscriber_task
    if _subscriber_task is None:
        return

    _subscriber_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await _subscriber_task
    _subscriber_task = None
    Logger.info(Messages.CACHE_BROADCAST_SUBSCRIBER_STOPPED)


def _handle_invalidation_message(data: Any) -> None:
    """解析失效广播并清理匹配命名空间的本地缓存条目

    广播携带 ids 或 user_ids 时按 id 段精确清理，否则整命名空间清理
    """
    try:
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        payload: Any = json.loads(data) if isinstance(data, str) else data
        namespace = payload.get("namespace") if isinstance(payload, dict) else None
        if not namespace:
            return

        ids = payload.get("ids") or []
        user_ids = payload.get("user_ids") or []
        cleared = 0
        for cache in list(_broadcast_caches):
            if str(namespace) != cache.INVALIDATION_NAMESPACE:
                continue
            if ids:
                cleared += cache.clear_local_ids([int(item) for item in ids])
            if user_ids:
                cleared += cache.clear_local_user_ids([int(item) for item in user_ids])
            if not ids and not user_ids:
                cleared += cache.clear_local_namespace(str(namespace))
    except Exception as e:
        Logger.error(Messages.CACHE_BROADCAST_INVALID_MESSAGE(e))


async def _cache_invalidation_loop() -> None:
    """订阅失效广播频道并持续分发清理指令，断线或异常时退出由重启兜底"""
    redis_client = get_redis_client()
    pubsub = await redis_client.get_pubsub()
    if pubsub is None:
        Logger.warning(Messages.CACHE_BROADCAST_SUBSCRIBER_UNAVAILABLE)
        return

    try:
        await pubsub.subscribe(RedisKeys.CACHE_INVALIDATE_CHANNEL)
        Logger.info(Messages.CACHE_BROADCAST_SUBSCRIBER_STARTED)
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message is None:
                continue
            if message.get("type") != "message":
                continue
            _handle_invalidation_message(message.get("data"))
    except asyncio.CancelledError:
        raise
    except Exception as e:
        Logger.error(Messages.CACHE_BROADCAST_LOOP_FAILED(e))
    finally:
        with contextlib.suppress(Exception):
            await pubsub.close()
