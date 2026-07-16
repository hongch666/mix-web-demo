from typing import List


class Defaults:
    """
    配置默认值类 — TTL、权重、超时
    """

    # ===== 缓存 =====
    CACHE_L1_TTL: int = 300
    CACHE_L2_TTL: int = 600

    # ===== 分布式锁 =====
    LOCK_DEFAULT_EXPIRE: int = 30
    LOCK_TASK_VECTOR_SYNC: str = "lock:task:vector:sync"
    LOCK_TASK_VECTOR_SYNC_EXPIRE: int = 86400
    LOCK_TASK_ANALYZE_CACHE: str = "lock:task:analyze:cache"
    LOCK_TASK_ANALYZE_CACHE_EXPIRE: int = 600
    LOCK_TASK_NEO4J_SYNC: str = "lock:task:neo4j:sync"
    LOCK_TASK_NEO4J_SYNC_EXPIRE: int = 3600

    # ===== 权限 =====
    ROLE_ADMIN: str = "admin"
    ROLE_USER: str = "user"

    # ===== 图谱搜索权重配置 =====
    GRAPH_TAG_INTEREST_WEIGHT: float = 0.35
    GRAPH_FOLLOWED_AUTHOR_WEIGHT: float = 0.25
    GRAPH_SAME_SUB_CATEGORY_WEIGHT: float = 0.20
    GRAPH_CANDIDATE_SIMILARITY_WEIGHT: float = 0.20
    GRAPH_KEYWORD_TAG_WEIGHT: float = 0.20

    # ===== 向量搜索配置 =====
    VECTOR_SEARCH_ENABLED: bool = True
    VECTOR_SEARCH_CANDIDATE_LIMIT: int = 50
    VECTOR_SEARCH_FETCH_MULTIPLIER: int = 4
    VECTOR_SEARCH_MAX_MATCHED_CHUNKS: int = 2
    VECTOR_SEARCH_MIN_SCORE: float = 0.3
    VECTOR_SEARCH_SCORE_MODE: str = "similarity"

    # ===== 权限关键词 =====
    PERSONAL_INFO_KEYWORDS: List[str] = [
        "我的",
        "个人",
        "自己的",
        "本人的",
        "我",
        "自己",
        "点赞",
        "收藏",
        "喜欢",
        "评论",
        "互动",
        "关注",
    ]
