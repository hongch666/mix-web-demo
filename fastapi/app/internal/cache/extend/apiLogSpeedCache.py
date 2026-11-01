from functools import lru_cache
from typing import Any, ClassVar

from app.core.base import LoggerProtocol
from app.core.constants import RedisKeys
from app.internal.models import AdsApiAverageSpeed

from ..versionedCache import VersionedCache


class ApiLogSpeedCache(VersionedCache[list[dict[str, Any]]]):
    """
    接口平均响应时间缓存 - 二级缓存架构（带版本控制）

    缓存策略：
    1. L1 缓存（本地内存）- 5分钟 TTL
    2. L2 缓存（Redis）- 1天 TTL
    3. 版本号检测 - 数仓平均响应时间表变化时自动失效
    """

    REDIS_KEY_PREFIX: str = RedisKeys.APILOG_AVERAGE_SPEED
    REDIS_VERSION_KEY: str = RedisKeys.APILOG_AVERAGE_SPEED_VERSION
    # 版本号校验依据：接口平均响应时间数仓表
    VERSION_MODEL: ClassVar[type[AdsApiAverageSpeed]] = AdsApiAverageSpeed


@lru_cache
def get_api_log_speed_cache(logger: LoggerProtocol | None = None) -> ApiLogSpeedCache:
    """获取 ApiLogSpeedCache 单例实例"""
    return ApiLogSpeedCache(logger)
