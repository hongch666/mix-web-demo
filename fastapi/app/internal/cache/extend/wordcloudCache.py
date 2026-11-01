from functools import lru_cache
from typing import ClassVar

from app.core.base import LoggerProtocol
from app.core.constants import Messages, RedisKeys
from app.internal.models import AdsSearchKeyword

from ..versionedCache import VersionedCache


class WordcloudCache(VersionedCache[str]):
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
    VERSION_MODEL: ClassVar[type[AdsSearchKeyword]] = AdsSearchKeyword

    MISS_LOG_MESSAGE: str = Messages.DB_CACHE_MISS_QUERY_DB_MESSAGE
    """未命中后需要重新生成词云图的日志消息"""


@lru_cache
def get_wordcloud_cache(logger: LoggerProtocol | None = None) -> WordcloudCache:
    """依赖注入 - 获取词云图缓存单例"""
    return WordcloudCache(logger)
