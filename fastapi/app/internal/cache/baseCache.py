import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from app.core.base import Constants, Logger
from app.core.db import get_redis_client


class BaseCache(ABC):
    """
    缓存基础模板类 - 二级缓存架构

    缓存策略：
    1. L1 缓存（本地内存）- 可配置 TTL
    2. L2 缓存（Redis）- 1天 TTL
    """

    # 子类需要定义这些常量
    REDIS_KEY_PREFIX: str = ""
    L1_CACHE_TTL: int = 300  # 默认5分钟

    def __init__(self) -> None:
        # L1 本地缓存
        self._local_cache: Optional[Any] = None
        self._local_cache_time: float = 0
        self._local_cache_ttl: int = self.L1_CACHE_TTL

        # Redis 客户端
        self._redis = get_redis_client()

        # Redis TTL（1天）
        self._redis_ttl: int = 86400

    def __repr__(self) -> str:
        """对象表示 - 用于日志输出和序列化"""
        return f"{self.__class__.__name__}()"

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}()"

    def is_local_cache_valid(self) -> bool:
        """检查本地缓存是否有效"""
        if not self._local_cache:
            return False

        # 检查 TTL
        if time.time() - self._local_cache_time > self._local_cache_ttl:
            Logger.info(Constants.L1_CACHE_TTL_EXPIRED)
            return False

        return True

    def get_from_local(self) -> Optional[Any]:
        """从本地缓存获取"""
        if self.is_local_cache_valid():
            cache_age = time.time() - self._local_cache_time
            Logger.info(f"[L1缓存] 命中，缓存年龄: {cache_age:.1f}s")
            return self._local_cache
        return None

    async def get_from_redis(self) -> Optional[Any]:
        """从 Redis 缓存获取"""
        try:
            data = await self._redis.get(self.REDIS_KEY_PREFIX)
            if data:
                Logger.info(Constants.L2_CACHE_HIT)
                # 同时更新本地缓存
                self._local_cache = data
                self._local_cache_time = time.time()
                return data

            Logger.info(Constants.L2_CACHE_MISS)
            return None
        except Exception as e:
            Logger.error(f"[L2缓存] Redis 读取失败: {e}")
            return None

    def update_local_cache(self, data: Any) -> None:
        """更新本地缓存"""
        self._local_cache = data
        self._local_cache_time = time.time()
        Logger.info(Constants.L1_CACHE_UPDATED)

    async def update_redis_cache(self, data: Any) -> None:
        """更新 Redis 缓存"""
        try:
            await self._redis.set(self.REDIS_KEY_PREFIX, data, ex=self._redis_ttl)
            Logger.info(f"[L2缓存] 已更新 Redis，TTL={self._redis_ttl}s (1天)")
        except Exception as e:
            Logger.error(f"[L2缓存] Redis 写入失败: {e}")

    def clear_local_cache(self) -> None:
        """清除本地缓存"""
        self._local_cache = None
        self._local_cache_time = 0
        Logger.info(Constants.L1_CACHE_CLEARED)

    async def clear_redis_cache(self) -> None:
        """清除 Redis 缓存"""
        try:
            await self._redis.delete(self.REDIS_KEY_PREFIX)
            Logger.info(Constants.L2_CACHE_CLEARED)
        except Exception as e:
            Logger.error(f"[L2缓存] Redis 清除失败: {e}")

    async def clear_all(self) -> None:
        """清除所有缓存"""
        self.clear_local_cache()
        await self.clear_redis_cache()

    @abstractmethod
    async def get(self) -> Optional[Any]:
        """获取缓存（需要子类实现）"""
        pass

    @abstractmethod
    async def set(self, data: Any) -> None:
        """设置缓存（需要子类实现）"""
        pass
