import time
from collections.abc import Awaitable, Callable
from typing import Any, Optional

from app.core.base import LoggerProtocol
from app.core.constants import Defaults, Messages

from .versionedCache import VersionedCache


class KeyedVersionedCache(VersionedCache[Any]):
    """按业务键分片的带版本控制缓存模板

    L1 用字典保存多份键值并按写入时间做 TTL 淘汰与容量上限控制，L2 每个键一个 Redis key；
    版本号仍按数仓表统一校验，版本变化时清空该缓存下的全部键
    """

    L1_MAX_ENTRIES: int = Defaults.L1_CACHE_MAX_ENTRIES
    """L1 本地缓存的最大条目数，子类可按需覆盖"""

    def __init__(self, logger: LoggerProtocol | None = None) -> None:
        """调用父类完成版本控制与 Redis 依赖初始化，并建立键分片的本地缓存容器"""
        super().__init__(logger)
        self._local_entries: dict[str, tuple[Any, float]] = {}

    async def get(self) -> Optional[Any]:
        """键分片缓存不提供无键读取入口"""
        raise NotImplementedError

    async def set(self, data: Any) -> None:
        """键分片缓存不提供无键写入入口"""
        raise NotImplementedError

    async def get_entry(self, key: str) -> Optional[Any]:
        """按业务键读取缓存，先校验版本号再依次查本地与 Redis"""
        if await self.is_version_changed():
            self._logger.info(Messages.VERSION_CHANGED_CLEAR_CACHE)
            await self.clear_all()
            return None

        local_value = self._read_local(key)
        if local_value is not None:
            return local_value

        return await self._read_redis(key)

    async def set_entry(self, key: str, data: Any) -> None:
        """按业务键写入两级缓存并提交版本号"""
        self._write_local(key, data)
        await self._write_redis(key, data)
        await self.update_version()

    async def get_entry_or_load(
        self, key: str, loader: Callable[[], Awaitable[Any]]
    ) -> Optional[Any]:
        """按键先读两级缓存，未命中时合并同 key 的并发回源并回填缓存"""
        cached: Optional[Any] = await self.get_entry(key)
        if cached is not None:
            return cached

        return await self._single_flight.do(key, lambda: self._load_entry(key, loader))

    async def _load_entry(
        self, key: str, loader: Callable[[], Awaitable[Any]]
    ) -> Optional[Any]:
        """单飞内二次确认缓存，仍未命中才回源，空结果不回填避免固化长期空集"""
        cached: Optional[Any] = await self.get_entry(key)
        if cached is not None:
            self._logger.debug(Messages.SINGLEFLIGHT_KEY_HIT(key))
            return cached

        result: Optional[Any] = await loader()
        if result:
            await self.set_entry(key, result)
        return result

    async def clear_all(self) -> None:
        """清空本地键值、Redis 中该前缀的全部键与版本号，按 SCAN 分批删除避免阻塞 Redis"""
        self._local_entries.clear()
        self._cache_version = None
        try:
            await self._redis.delete_by_patterns(f"{self.REDIS_KEY_PREFIX}*")
            await self._redis.delete(self.REDIS_VERSION_KEY)
        except Exception as e:
            self._logger.error(Messages.CACHE_L2_CLEAR_FAILED(e))

    def _read_local(self, key: str) -> Optional[Any]:
        """读取未过期的本地键值，过期条目顺手清理"""
        entry = self._local_entries.get(key)
        if entry is None:
            return None
        value, created_at = entry
        cache_age = time.time() - created_at
        if cache_age > self._local_cache_ttl:
            self._local_entries.pop(key, None)
            self._logger.info(Messages.L1_CACHE_TTL_EXPIRED)
            return None
        self._logger.info(Messages.CACHE_L1_HIT(cache_age))
        return value

    def _write_local(self, key: str, data: Any) -> None:
        """写入本地键值，超出容量上限时淘汰最早写入的条目"""
        if (
            len(self._local_entries) >= self.L1_MAX_ENTRIES
            and key not in self._local_entries
        ):
            oldest_key = min(
                self._local_entries, key=lambda item: self._local_entries[item][1]
            )
            self._local_entries.pop(oldest_key, None)
        self._local_entries[key] = (data, time.time())
        self._logger.info(Messages.L1_CACHE_UPDATED)

    async def _read_redis(self, key: str) -> Optional[Any]:
        """按业务键读取 Redis 缓存，命中时回填本地缓存"""
        try:
            data = await self._redis.get(f"{self.REDIS_KEY_PREFIX}{key}")
            if data is not None:
                self._logger.info(Messages.L2_CACHE_HIT)
                self._write_local(key, data)
                return data
            self._logger.info(Messages.L2_CACHE_MISS)
            return None
        except Exception as e:
            self._logger.error(Messages.CACHE_L2_READ_FAILED(e))
            return None

    async def _write_redis(self, key: str, data: Any) -> None:
        """按业务键写入 Redis 缓存，失败只记录日志"""
        try:
            await self._redis.set(
                f"{self.REDIS_KEY_PREFIX}{key}", data, ex=self._redis_ttl
            )
            self._logger.info(Messages.CACHE_L2_UPDATED(self._redis_ttl))
        except Exception as e:
            self._logger.error(Messages.CACHE_L2_WRITE_FAILED(e))
