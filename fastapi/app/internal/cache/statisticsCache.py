from functools import lru_cache
from typing import Any, Dict, Optional

from app.core.base import Constants, Logger

from .baseCache import BaseCache

# 全局单例实例
_statistics_cache_instance = None


class StatisticsCache(BaseCache):
    """
    文章统计信息缓存 - 二级缓存架构

    缓存策略：
    1. L1 缓存（本地内存）- 10分钟 TTL
    2. L2 缓存（Redis）- 1天 TTL
    """

    # Redis 键前缀
    REDIS_KEY_PREFIX: str = "article:statistics"
    L1_CACHE_TTL: int = 600  # 10分钟

    def get(self) -> Optional[Dict[str, Any]]:
        """
        获取缓存（二级缓存）

        查找顺序：
        1. 本地内存缓存（L1）
        2. Redis 缓存（L2）
        3. 返回 None（需要查询 DB）
        """
        # 1. 先查本地缓存
        local_data = self.get_from_local()
        if local_data:
            return local_data

        # 2. 本地缓存失效，查 Redis
        redis_data = self.get_from_redis()
        if redis_data:
            return redis_data

        # 3. 两级缓存都没有
        Logger.info(Constants.DB_CACHE_MISS_QUERY_DB_MESSAGE)
        return None

    def set(self, data: Dict[str, Any]) -> None:
        """
        设置缓存（二级缓存）

        同时更新：
        1. 本地内存缓存（L1）
        2. Redis 缓存（L2）
        """
        self.update_local_cache(data)
        self.update_redis_cache(data)


@lru_cache()
def get_statistics_cache() -> StatisticsCache:
    """获取 StatisticsCache 单例实例"""
    global _statistics_cache_instance
    if _statistics_cache_instance is None:
        _statistics_cache_instance = StatisticsCache()
    return _statistics_cache_instance
