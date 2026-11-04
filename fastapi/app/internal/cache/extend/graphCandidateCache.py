from functools import lru_cache
from typing import Any, Optional

from app.core.constants import RedisKeys

from ..pubSubCache import KeyedPubSubCache


class GraphCandidateCache(KeyedPubSubCache[Optional[list[dict[str, Any]]]]):
    """候选间相似标签信号的两级缓存（按候选批次粒度）

    该信号的打分依赖整个候选集合（候选两两之间的共享标签），无法拆成单文章键，
    因此按候选集合 hash 为批次键缓存，图谱同步发生文章或用户维度变更时整体失效
    """

    REDIS_KEY_PREFIX: str = RedisKeys.GRAPH_CANDIDATE_CACHE_PREFIX
    INVALIDATION_NAMESPACE: str = RedisKeys.CACHE_NAMESPACE_CANDIDATE


@lru_cache
def get_graph_candidate_cache() -> GraphCandidateCache:
    """获取候选相似标签缓存单例"""
    return GraphCandidateCache()
