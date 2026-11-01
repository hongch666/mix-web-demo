from functools import lru_cache
from typing import Any, ClassVar

from app.core.base import LoggerProtocol
from app.core.constants import RedisKeys
from app.internal.models import AdsCategoryStats

from ..versionedCache import VersionedCache


class CategoryCache(VersionedCache[list[dict[str, Any]]]):
    """
    分类文章数缓存管理 - 二级缓存架构（带版本控制）

    缓存策略：
    1. L1 缓存（本地内存）- 5分钟 TTL
    2. L2 缓存（Redis）- 1天 TTL
    3. 版本号检测 - ClickHouse 表变化时自动失效
    """

    # Redis 键前缀
    REDIS_KEY_PREFIX: str = RedisKeys.CATEGORY_ARTICLE_COUNT
    REDIS_VERSION_KEY: str = RedisKeys.CATEGORY_ARTICLE_COUNT_VERSION
    L1_CACHE_TTL: int = 300  # 5分钟

    # 版本号校验依据：分类文章数数仓表
    VERSION_MODEL: ClassVar[type[AdsCategoryStats]] = AdsCategoryStats


@lru_cache
def get_category_cache(logger: LoggerProtocol | None = None) -> CategoryCache:
    """获取 CategoryCache 单例实例"""
    return CategoryCache(logger)
