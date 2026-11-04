from functools import lru_cache
from typing import Any, Optional

from app.core.constants import RedisKeys

from ..pubSubCache import KeyedPubSubCache


class VectorQueryCache(KeyedPubSubCache[Optional[list[dict[str, Any]]]]):
    """向量检索 ANN 结果的两级缓存

    以归一化查询文本与 fetch_k 的 hash 为键缓存 pgvector 检索结果，
    向量同步完成后整体失效并广播；候选集交集仍由请求现算，不落缓存
    """

    REDIS_KEY_PREFIX: str = RedisKeys.VECTOR_ENHANCE_CACHE_PREFIX
    INVALIDATION_NAMESPACE: str = RedisKeys.CACHE_NAMESPACE_VECTOR


@lru_cache
def get_vector_query_cache() -> VectorQueryCache:
    """获取向量检索缓存单例"""
    return VectorQueryCache()
