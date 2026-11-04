from functools import lru_cache
from typing import Any, Optional

from app.core.constants import RedisKeys

from ..pubSubCache import KeyedPubSubCache


class GraphSignalCache(KeyedPubSubCache[Optional[list[dict[str, Any]]]]):
    """图谱增强个性化信号的两级缓存（按单文章粒度）

    缓存兴趣标签、关注作者、同子分类与关键词标签四路信号的 Neo4j 查询原始行，
    键形为「信号名:文章 id:用户 id（或关键词 hash）」，文章 id 为完整冒号段落，
    因此可按变更文章 id 精确失效；用户行为变更按用户 id 后缀失效
    """

    REDIS_KEY_PREFIX: str = RedisKeys.GRAPH_SIGNAL_CACHE_PREFIX
    INVALIDATION_NAMESPACE: str = RedisKeys.CACHE_NAMESPACE_GRAPH


@lru_cache
def get_graph_signal_cache() -> GraphSignalCache:
    """获取图谱信号缓存单例"""
    return GraphSignalCache()
