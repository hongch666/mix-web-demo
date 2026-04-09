import time
from functools import lru_cache
from typing import Optional

from app.core.base import Constants, Logger

from .baseCache import BaseCache

# 全局单例实例
_wordcloud_cache_instance = None


class WordcloudCache(BaseCache):
    """
    词云图缓存管理 - 二级缓存架构

    缓存策略：
    1. L1 缓存（本地内存）- 5分钟 TTL
    2. L2 缓存（Redis）- 1天 TTL
    """

    # Redis 键前缀
    REDIS_KEY_PREFIX: str = "wordcloud:url"
    L1_CACHE_TTL: int = 300  # 5分钟

    async def get_from_redis(self) -> Optional[str]:
        """从 Redis 缓存获取"""
        try:
            data = await self._redis.get(self.REDIS_KEY_PREFIX)
            if data:
                Logger.info(Constants.L2_CACHE_HIT)
                # 统一转换为字符串类型
                url = data if isinstance(data, str) else str(data)
                # 同时更新本地缓存
                self._local_cache = url
                self._local_cache_time = time.time()
                return url

            Logger.info(Constants.L2_CACHE_MISS)
            return None
        except Exception as e:
            Logger.error(f"[L2缓存] Redis 读取失败: {e}")
            return None

    async def get(self) -> Optional[str]:
        """
        获取词云图OSS URL缓存（二级缓存）

        查找顺序：
        1. 本地内存缓存（L1）
        2. Redis 缓存（L2）
        3. 返回 None（需要重新生成）
        """
        # 1. 先查本地缓存
        local_data = self.get_from_local()
        if local_data:
            return local_data

        # 2. 本地缓存失效，查 Redis
        redis_data = await self.get_from_redis()
        if redis_data:
            return redis_data

        # 3. 两级缓存都没有
        Logger.info(Constants.DB_CACHE_MISS_QUERY_DB_MESSAGE)
        return None

    async def set(self, oss_url: str) -> None:
        """
        设置词云图OSS URL缓存（二级缓存）

        同时更新：
        1. 本地内存缓存（L1）
        2. Redis 缓存（L2）

        参数:
            oss_url: OSS中词云图的URL
        """
        self.update_local_cache(oss_url)
        await self.update_redis_cache(oss_url)

    async def delete(self) -> None:
        """删除所有级别的词云图缓存"""
        self.clear_local_cache()
        try:
            await self._redis.delete(self.REDIS_KEY_PREFIX)
            Logger.info(Constants.WORDCLOUD_CACHE_DELETED)
        except Exception as e:
            Logger.error(f"[L2缓存] Redis 清除失败: {e}")


@lru_cache
def get_wordcloud_cache() -> WordcloudCache:
    """依赖注入 - 获取词云图缓存单例"""
    global _wordcloud_cache_instance
    if _wordcloud_cache_instance is None:
        _wordcloud_cache_instance = WordcloudCache()
    return _wordcloud_cache_instance
