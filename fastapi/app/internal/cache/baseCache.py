import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any, Optional

from app.core.base import Logger, LoggerProtocol
from app.core.constants import Defaults, Messages
from app.core.db import get_redis_client

from .singleFlight import SingleFlight


class BaseCache[T](ABC):
    """
    缓存基础模板类 - 二级缓存架构

    缓存策略：
    1. L1 缓存（本地内存）- 可配置 TTL
    2. L2 缓存（Redis）- 1天 TTL
    """

    # 子类需要定义这些常量

    REDIS_KEY_PREFIX: str = ""
    """Redis 缓存键前缀，子类必须覆盖"""
    L1_CACHE_TTL: int = Defaults.L1_CACHE_TTL
    """L1 本地缓存 TTL（秒），子类可按需覆盖"""
    L2_CACHE_TTL: int = Defaults.L2_CACHE_TTL
    """L2 Redis 缓存 TTL（秒），子类可按需覆盖"""

    def __init__(self, logger: LoggerProtocol | None = None) -> None:
        """初始化 L1 本地缓存槽、Redis 客户端、两级缓存 TTL 与可注入的日志器"""

        # L1 本地缓存
        self._local_cache: Optional[T] = None
        self._local_cache_time: float = 0
        self._local_cache_ttl: int = self.L1_CACHE_TTL
        # 是否写入过 L1：用独立标记区分「从未写入」与「写入了 0、[]、""、False 等合法假值」
        self._local_cache_present: bool = False

        # 同 key 并发回源合并，避免热点键过期瞬间击穿到数仓或图库
        self._single_flight: SingleFlight = SingleFlight()

        # Redis 客户端
        self._redis = get_redis_client()

        # Redis TTL（默认 1 天）
        self._redis_ttl: int = self.L2_CACHE_TTL

        # 日志器可注入，缺省回退全局单例
        self._logger: LoggerProtocol = logger or Logger

    def __repr__(self) -> str:
        """对象表示 - 用于日志输出和序列化"""
        return f"{self.__class__.__name__}()"

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}()"

    async def is_local_cache_valid(self) -> bool:
        """检查本地缓存是否有效，只以写入标记与 TTL 判断，不看缓存值本身是否为真"""
        if not self._local_cache_present:
            return False

        # 检查 TTL
        if time.time() - self._local_cache_time > self._local_cache_ttl:
            self._logger.info(Messages.L1_CACHE_TTL_EXPIRED)
            return False

        return True

    async def get_from_local(self) -> Optional[T]:
        """从本地缓存获取"""
        if await self.is_local_cache_valid():
            cache_age = time.time() - self._local_cache_time
            self._logger.info(Messages.CACHE_L1_HIT(cache_age))
            return self._local_cache
        return None

    async def get_from_redis(self) -> Optional[T]:
        """从 Redis 缓存获取，仅以 None 表示未命中，0、[]、""、False 等假值同样是有效缓存"""
        try:
            data: Optional[T] = await self._redis.get(self.REDIS_KEY_PREFIX)
            if data is not None:
                self._logger.info(Messages.L2_CACHE_HIT)
                # 同时更新本地缓存
                self._local_cache = data
                self._local_cache_time = time.time()
                self._local_cache_present = True
                return data

            self._logger.info(Messages.L2_CACHE_MISS)
            return None
        except Exception as e:
            self._logger.error(Messages.CACHE_L2_READ_FAILED(e))
            return None

    async def update_local_cache(self, data: T) -> None:
        """更新本地缓存"""
        self._local_cache = data
        self._local_cache_time = time.time()
        self._local_cache_present = True
        self._logger.info(Messages.L1_CACHE_UPDATED)

    async def update_redis_cache(self, data: T) -> None:
        """更新 Redis 缓存"""
        try:
            await self._redis.set(self.REDIS_KEY_PREFIX, data, ex=self._redis_ttl)
            self._logger.info(Messages.CACHE_L2_UPDATED(self._redis_ttl))
        except Exception as e:
            self._logger.error(Messages.CACHE_L2_WRITE_FAILED(e))

    async def clear_local_cache(self) -> None:
        """清除本地缓存"""
        self._local_cache = None
        self._local_cache_time = 0
        self._local_cache_present = False
        self._logger.info(Messages.L1_CACHE_CLEARED)

    async def clear_redis_cache(self) -> None:
        """清除 Redis 缓存"""
        try:
            await self._redis.delete(self.REDIS_KEY_PREFIX)
            self._logger.info(Messages.L2_CACHE_CLEARED)
        except Exception as e:
            self._logger.error(Messages.CACHE_L2_CLEAR_FAILED(e))

    async def clear_all(self) -> None:
        """清除所有缓存"""
        await self.clear_local_cache()
        await self.clear_redis_cache()

    async def get_or_load(
        self, loader: Callable[[], Awaitable[Optional[T]]]
    ) -> Optional[T]:
        """先读两级缓存，未命中时把同 key 的并发回源合并为一次并回填缓存

        loader 为空结果时只返回不回填，保持既有「空结果不进长期缓存」的约定；
        负缓存需要短 TTL 的场景由各模板的 set_entry / set_entries 显式控制。
        """
        cached: Optional[T] = await self.get()
        if cached is not None:
            return cached

        return await self._single_flight.do(
            self.REDIS_KEY_PREFIX, lambda: self._load_and_fill(loader)
        )

    async def run_single_flight(
        self, key: str, loader: Callable[[], Awaitable[Any]]
    ) -> Any:
        """按键合并并发回源，供批量缓存等无法直接套用 get_or_load 的场景复用"""
        return await self._single_flight.do(key, loader)

    async def _load_and_fill(
        self, loader: Callable[[], Awaitable[Optional[T]]]
    ) -> Optional[T]:
        """单飞内二次确认缓存，仍未命中才回源，保证合并后的等待者拿到同一结果"""
        cached: Optional[T] = await self.get()
        if cached is not None:
            self._logger.debug(Messages.SINGLEFLIGHT_KEY_HIT(self.REDIS_KEY_PREFIX))
            return cached

        result: Optional[T] = await loader()
        if result:
            await self.set(result)
        return result

    @abstractmethod
    async def get(self) -> Optional[T]:
        """获取缓存（需要子类实现）"""
        pass

    @abstractmethod
    async def set(self, data: T) -> None:
        """设置缓存（需要子类实现）"""
        pass
