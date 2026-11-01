from functools import lru_cache
from typing import Any, ClassVar

from app.core.base import LoggerProtocol
from app.core.constants import RedisKeys
from app.internal.models import AdsMonthlyPublish

from ..versionedCache import VersionedCache


class PublishTimeCache(VersionedCache[list[dict[str, Any]]]):
    """
    文章发布时间缓存管理 - 二级缓存架构（带版本控制）

    缓存策略：
    1. L1 缓存（本地内存）- 5分钟 TTL
    2. L2 缓存（Redis）- 1天 TTL
    3. 版本号检测 - ClickHouse 表变化时自动失效
    """

    # Redis 键前缀
    REDIS_KEY_PREFIX: str = RedisKeys.PUBLISH_MONTHLY_COUNT
    REDIS_VERSION_KEY: str = RedisKeys.PUBLISH_MONTHLY_COUNT_VERSION

    # 版本号校验依据：月度发布数数仓表
    VERSION_MODEL: ClassVar[type[AdsMonthlyPublish]] = AdsMonthlyPublish


@lru_cache
def get_publish_time_cache(logger: LoggerProtocol | None = None) -> PublishTimeCache:
    """获取 PublishTimeCache 单例实例"""
    return PublishTimeCache(logger)
