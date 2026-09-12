import time
from functools import lru_cache
from typing import Optional

from app.core.base import Logger
from app.core.constants import Messages, RedisKeys
from app.internal.models import AdsSearchKeyword

from ..versionedCache import VersionedCache

# 全局单例实例
_wordcloud_cache_instance = None


class WordcloudCache(VersionedCache):
    """
    词云图缓存管理 - 二级缓存架构（带版本控制）

    缓存策略：
    1. L1 缓存（本地内存）- 5分钟 TTL
    2. L2 缓存（Redis）- 1天 TTL
    3. 版本号检测 - ClickHouse 搜索关键词表变化时自动失效
    """

    # Redis 键前缀
    REDIS_KEY_PREFIX: str = RedisKeys.WORDCLOUD_URL
    REDIS_VERSION_KEY: str = RedisKeys.WORDCLOUD_URL_VERSION
    L1_CACHE_TTL: int = 300  # 5分钟

    # 版本号校验依据：搜索关键词数仓表
    VERSION_MODEL: type[AdsSearchKeyword] = AdsSearchKeyword

    async def get_from_redis(self) -> Optional[str]:
        """从 Redis 缓存获取"""
        try:
            data = await self._redis.get(self.REDIS_KEY_PREFIX)
            if data:
                Logger.info(Messages.L2_CACHE_HIT)
                # 统一转换为字符串类型
                url = data if isinstance(data, str) else str(data)
                # 同时更新本地缓存
                self._local_cache = url
                self._local_cache_time = time.time()
                return url

            Logger.info(Messages.L2_CACHE_MISS)
            return None
        except Exception as e:
            Logger.error(Messages.CACHE_L2_READ_FAILED(e))
            return None

    async def get(self) -> Optional[str]:
        """
        获取词云图OSS URL缓存（二级缓存）

        查找顺序：
        1. 版本号校验，数仓搜索关键词表变化时缓存失效
        2. 本地内存缓存（L1）
        3. Redis 缓存（L2）
        4. 返回 None（需要重新生成）
        """
        # 检查版本号是否变化
        if await self.is_version_changed():
            Logger.info(Messages.VERSION_CHANGED_CLEAR_CACHE)
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
        Logger.info(Messages.DB_CACHE_MISS_QUERY_DB_MESSAGE)
        return None

    async def set(self, oss_url: str) -> None:
        """
        设置词云图OSS URL缓存（二级缓存）

        同时更新：
        1. 本地内存缓存（L1）
        2. Redis 缓存（L2）
        3. 版本号

        参数:
            oss_url: OSS中词云图的URL
        """
        # 更新两级缓存
        await self.update_local_cache(oss_url)
        await self.update_redis_cache(oss_url)

        # 更新版本号
        await self.update_version()


@lru_cache
def get_wordcloud_cache() -> WordcloudCache:
    """依赖注入 - 获取词云图缓存单例"""
    global _wordcloud_cache_instance
    if _wordcloud_cache_instance is None:
        _wordcloud_cache_instance = WordcloudCache()
    return _wordcloud_cache_instance
