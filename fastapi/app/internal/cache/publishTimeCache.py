from functools import lru_cache
from typing import Any, Dict, List, Optional

from app.core.base import Constants, Logger

from .versionedCache import VersionedCache

# 全局单例实例
_publish_time_cache_instance = None


class PublishTimeCache(VersionedCache):
    """
    文章发布时间缓存管理 - 二级缓存架构（带版本控制）

    缓存策略：
    1. L1 缓存（本地内存）- 5分钟 TTL
    2. L2 缓存（Redis）- 1天 TTL
    3. 版本号检测 - ClickHouse 表变化时自动失效
    """

    # Redis 键前缀
    REDIS_KEY_PREFIX: str = "publish:monthly_count"
    REDIS_VERSION_KEY: str = "publish:monthly_count:version"
    L1_CACHE_TTL: int = 300  # 5分钟

    async def get(self, ch_conn: Any) -> Optional[List[Dict[str, Any]]]:
        """
        获取缓存（二级缓存）

        查找顺序：
        1. 本地内存缓存（L1）
        2. Redis 缓存（L2）
        3. 返回 None（需要查询 ClickHouse）
        """
        # 检查版本号是否变化
        if await self.is_version_changed(ch_conn):
            Logger.info(Constants.VERSION_CHANGED_CLEAR_CACHE)
            await self.clear_all()
            return None

        # 1. 先查本地缓存
        local_data = await self.get_from_local()
        if local_data:
            return local_data

        # 2. 本地缓存失效，查 Redis
        redis_data = await self.get_from_redis()
        if redis_data:
            return redis_data

        # 3. 两级缓存都没有
        Logger.info(Constants.CLICKHOUSE_CACHE_MISS_QUERY_MESSAGE)
        return None

    async def set(self, data: List[Dict[str, Any]], ch_conn: Any) -> None:
        """
        设置缓存（二级缓存）

        同时更新：
        1. 本地内存缓存（L1）
        2. Redis 缓存（L2）
        3. 版本号
        """
        # 更新两级缓存
        await self.update_local_cache(data)
        await self.update_redis_cache(data)

        # 更新版本号
        await self.update_version(ch_conn)


@lru_cache()
def get_publish_time_cache() -> PublishTimeCache:
    """获取 PublishTimeCache 单例实例"""
    global _publish_time_cache_instance
    if _publish_time_cache_instance is None:
        _publish_time_cache_instance = PublishTimeCache()
    return _publish_time_cache_instance
