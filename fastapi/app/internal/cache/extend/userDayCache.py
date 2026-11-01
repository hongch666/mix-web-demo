from functools import lru_cache
from typing import ClassVar

from app.core.base import LoggerProtocol
from app.core.constants import RedisKeys
from app.internal.models import AdsUserDay

from ..keyedVersionedCache import KeyedVersionedCache


class UserDayCache(KeyedVersionedCache):
    """
    用户日趋势缓存 - 按键分片的二级缓存（带版本控制）

    缓存策略：
    1. L1 缓存（本地内存，多键）- 5分钟 TTL
    2. L2 缓存（Redis，每键一个 key）- 1天 TTL
    3. 版本号检测 - 用户日聚合表变化时清空全部键
    """

    REDIS_KEY_PREFIX: str = RedisKeys.USER_DAY_TREND_PREFIX
    REDIS_VERSION_KEY: str = RedisKeys.USER_DAY_TREND_VERSION
    L1_CACHE_TTL: int = 300

    # 版本号校验依据：用户日聚合数仓表
    VERSION_MODEL: ClassVar[type[AdsUserDay]] = AdsUserDay


@lru_cache
def get_user_day_cache(logger: LoggerProtocol | None = None) -> UserDayCache:
    """获取 UserDayCache 单例实例"""
    return UserDayCache(logger)
