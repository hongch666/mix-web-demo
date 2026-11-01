from functools import lru_cache
from typing import ClassVar

from app.core.base import LoggerProtocol
from app.core.constants import RedisKeys
from app.internal.models import AdsUserStats

from ..keyedVersionedCache import KeyedVersionedCache


class UserStatsCache(KeyedVersionedCache):
    """
    用户统计总览缓存 - 按键分片的二级缓存（带版本控制）

    缓存策略：
    1. L1 缓存（本地内存，多键）- 10分钟 TTL
    2. L2 缓存（Redis，每键一个 key）- 1天 TTL
    3. 版本号检测 - 用户统计快照表变化时清空全部键
    """

    REDIS_KEY_PREFIX: str = RedisKeys.USER_STATS_PREFIX
    REDIS_VERSION_KEY: str = RedisKeys.USER_STATS_VERSION
    L1_CACHE_TTL: int = 600

    # 版本号校验依据：用户统计快照数仓表
    VERSION_MODEL: ClassVar[type[AdsUserStats]] = AdsUserStats


@lru_cache
def get_user_stats_cache(logger: LoggerProtocol | None = None) -> UserStatsCache:
    """获取 UserStatsCache 单例实例"""
    return UserStatsCache(logger)
