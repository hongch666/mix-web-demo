from functools import lru_cache
from typing import ClassVar

from app.core.base import LoggerProtocol
from app.core.constants import RedisKeys
from app.internal.models import AdsUserViewArticle

from ..keyedVersionedCache import KeyedVersionedCache


class UserViewCache(KeyedVersionedCache):
    """
    用户文章阅读分布缓存 - 按键分片的二级缓存（带版本控制）

    缓存策略：
    1. L1 缓存（本地内存，多键）- 5分钟 TTL
    2. L2 缓存（Redis，每键一个 key）- 1天 TTL
    3. 版本号检测 - 用户文章阅读分布表变化时清空全部键
    """

    REDIS_KEY_PREFIX: str = RedisKeys.USER_VIEW_DISTRIBUTION_PREFIX
    REDIS_VERSION_KEY: str = RedisKeys.USER_VIEW_DISTRIBUTION_VERSION
    # 版本号校验依据：用户文章阅读分布数仓表
    VERSION_MODEL: ClassVar[type[AdsUserViewArticle]] = AdsUserViewArticle


@lru_cache
def get_user_view_cache(logger: LoggerProtocol | None = None) -> UserViewCache:
    """获取 UserViewCache 单例实例"""
    return UserViewCache(logger)
