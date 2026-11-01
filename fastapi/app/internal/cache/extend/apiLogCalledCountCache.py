from functools import lru_cache
from typing import Any, ClassVar

from app.core.base import LoggerProtocol
from app.core.constants import RedisKeys
from app.internal.models import AdsApiCalledCount

from ..versionedCache import VersionedCache


class ApiLogCalledCountCache(VersionedCache[list[dict[str, Any]]]):
    """
    接口调用次数缓存 - 二级缓存架构（带版本控制）

    缓存策略：
    1. L1 缓存（本地内存）- 5分钟 TTL
    2. L2 缓存（Redis）- 1天 TTL
    3. 版本号检测 - 数仓调用次数表变化时自动失效
    """

    REDIS_KEY_PREFIX: str = RedisKeys.APILOG_CALLED_COUNT
    REDIS_VERSION_KEY: str = RedisKeys.APILOG_CALLED_COUNT_VERSION
    L1_CACHE_TTL: int = 300

    # 版本号校验依据：接口调用次数数仓表
    VERSION_MODEL: ClassVar[type[AdsApiCalledCount]] = AdsApiCalledCount


@lru_cache
def get_api_log_called_count_cache(
    logger: LoggerProtocol | None = None,
) -> ApiLogCalledCountCache:
    """获取 ApiLogCalledCountCache 单例实例"""
    return ApiLogCalledCountCache(logger)
