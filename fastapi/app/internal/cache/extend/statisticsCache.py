from functools import lru_cache
from typing import Any, ClassVar

from app.core.base import LoggerProtocol
from app.core.constants import Messages, RedisKeys
from app.internal.models import AdsPlatformStats

from ..versionedCache import VersionedCache


class StatisticsCache(VersionedCache[dict[str, Any]]):
    """
    文章统计信息缓存 - 二级缓存架构（带版本控制）

    缓存策略：
    1. L1 缓存（本地内存）- 5分钟 TTL
    2. L2 缓存（Redis）- 1天 TTL
    3. 版本号检测 - ClickHouse 平台统计表变化时自动失效
    """

    # Redis 键前缀
    REDIS_KEY_PREFIX: str = RedisKeys.ARTICLE_STATISTICS
    REDIS_VERSION_KEY: str = RedisKeys.ARTICLE_STATISTICS_VERSION
    # 版本号校验依据：平台统计数仓表
    VERSION_MODEL: ClassVar[type[AdsPlatformStats]] = AdsPlatformStats

    MISS_LOG_MESSAGE: str = Messages.DB_CACHE_MISS_QUERY_DB_MESSAGE
    """未命中后回源查询 PostgreSQL 统计结果的日志消息"""


@lru_cache
def get_statistics_cache(logger: LoggerProtocol | None = None) -> StatisticsCache:
    """获取 StatisticsCache 单例实例"""
    return StatisticsCache(logger)
