from functools import lru_cache
from typing import Any, ClassVar

from app.core.base import LoggerProtocol
from app.core.constants import RedisKeys
from app.internal.models import AdsTop10Article

from ..versionedCache import VersionedCache


class ArticleCache(VersionedCache[list[dict[str, Any]]]):
    """
    文章缓存管理 - 二级缓存架构（带版本控制）

    缓存策略：
    1. L1 缓存（本地内存）- 5分钟 TTL
    2. L2 缓存（Redis）- 1天 TTL
    3. 版本号检测 - ClickHouse 表变化时自动失效
    """

    # Redis 键前缀
    REDIS_KEY_PREFIX: str = RedisKeys.ARTICLE_TOP10
    REDIS_VERSION_KEY: str = RedisKeys.ARTICLE_TOP10_VERSION

    # 版本号校验依据：文章 Top10 数仓表
    VERSION_MODEL: ClassVar[type[AdsTop10Article]] = AdsTop10Article


@lru_cache
def get_article_cache(logger: LoggerProtocol | None = None) -> ArticleCache:
    """获取 ArticleCache 单例实例"""
    return ArticleCache(logger)
