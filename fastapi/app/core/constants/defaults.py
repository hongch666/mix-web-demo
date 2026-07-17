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
    PERSONAL_INFO_KEYWORDS: list = [
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

    # ===== 搜索权重=====
    SEARCH_ES_SCORE_WEIGHT: float = 0.25
    SEARCH_AI_RATING_WEIGHT: float = 0.15
    SEARCH_USER_RATING_WEIGHT: float = 0.10
    SEARCH_VIEWS_WEIGHT: float = 0.08
    SEARCH_LIKES_WEIGHT: float = 0.08
    SEARCH_COLLECTS_WEIGHT: float = 0.08
    SEARCH_AUTHOR_FOLLOW_WEIGHT: float = 0.04
    SEARCH_RECENCY_WEIGHT: float = 0.22
    SEARCH_VECTOR_SCORE_WEIGHT: float = 0.25
    SEARCH_GRAPH_SCORE_WEIGHT: float = 0.20
    SEARCH_HYBRID_MIN_ES_WEIGHT: float = 0.55
    SEARCH_MAX_VIEWS_NORMALIZED: float = 10000.0
    SEARCH_MAX_LIKES_NORMALIZED: float = 1000.0
    SEARCH_MAX_COLLECTS_NORMALIZED: float = 1000.0
    SEARCH_MAX_FOLLOWS_NORMALIZED: float = 5000.0
    SEARCH_RECENCY_DECAY_DAYS: int = 30
