class RedisKeys:
    """
    Redis key 常量类 — 集中定义项目内所有 Redis key / 前缀 / 模式，作为唯一来源。

    此前这些 key 散落在各缓存子类、任务模块以及 messages.py / defaults.py 两处，
    其中分布式锁 key 还在两个常量文件里重复定义、引用也不一致。
    统一收口到本类后：
    - 修改前缀只需改这一处；
    - 消除 lock:task:* 的重复定义与引用不一致问题
    """

    # ===== 缓存 key =====

    @staticmethod
    def article_content_hash(article_id: int) -> str:
        """文章内容 hash 的完整 key"""
        return f"{RedisKeys.ARTICLE_CONTENT_HASH_PREFIX}{article_id}"

    ARTICLE_TOP10: str = "article:top10"
    """文章阅读量前十榜单的缓存 key"""

    ARTICLE_TOP10_VERSION: str = "article:top10:version"
    """前十榜单缓存的版本号，版本变化即代表缓存失效"""

    CATEGORY_ARTICLE_COUNT: str = "category:article_count"
    """分类文章数统计的缓存 key"""

    CATEGORY_ARTICLE_COUNT_VERSION: str = "category:article_count:version"
    """分类文章数统计的版本号"""

    PUBLISH_MONTHLY_COUNT: str = "publish:monthly_count"
    """每月发布量统计的缓存 key"""

    PUBLISH_MONTHLY_COUNT_VERSION: str = "publish:monthly_count:version"
    """每月发布量统计的版本号"""

    ARTICLE_STATISTICS: str = "article:statistics"
    """文章统计信息的缓存 key"""

    ARTICLE_STATISTICS_VERSION: str = "article:statistics:version"
    """文章统计信息的版本号"""

    WORDCLOUD_URL: str = "wordcloud:url"
    """词云图地址的缓存 key"""

    WORDCLOUD_URL_VERSION: str = "wordcloud:url:version"
    """词云图地址的版本号"""

    APILOG_AVERAGE_SPEED: str = "apilog:average_speed"
    """接口平均响应时间统计的缓存 key"""

    APILOG_AVERAGE_SPEED_VERSION: str = "apilog:average_speed:version"
    """接口平均响应时间统计的版本号"""

    APILOG_CALLED_COUNT: str = "apilog:called_count"
    """接口调用次数统计的缓存 key"""

    APILOG_CALLED_COUNT_VERSION: str = "apilog:called_count:version"
    """接口调用次数统计的版本号"""

    USER_DAY_TREND_PREFIX: str = "user:day_trend:"
    """用户日趋势的缓存 key 前缀，运行时拼接用户与指标"""

    USER_DAY_TREND_VERSION: str = "user:day_trend:version"
    """用户日趋势的版本号"""

    USER_STATS_PREFIX: str = "user:stats:"
    """用户统计总览的缓存 key 前缀，运行时拼接用户"""

    USER_STATS_VERSION: str = "user:stats:version"
    """用户统计总览的版本号"""

    USER_VIEW_DISTRIBUTION_PREFIX: str = "user:view_distribution:"
    """用户文章阅读分布的缓存 key 前缀，运行时拼接用户"""

    USER_VIEW_DISTRIBUTION_VERSION: str = "user:view_distribution:version"
    """用户文章阅读分布的版本号"""

    CACHE_INVALIDATE_CHANNEL: str = "cache:invalidate"
    """多级缓存跨实例失效广播频道，失效方发布命名空间，订阅方清理各自的本地条目"""

    CACHE_NAMESPACE_VECTOR: str = "vector"
    """向量检索缓存的失效命名空间"""

    CACHE_NAMESPACE_GRAPH: str = "graph"
    """图谱个性化信号缓存的失效命名空间"""

    CACHE_NAMESPACE_CANDIDATE: str = "graph_candidate"
    """候选相似标签批次缓存的失效命名空间"""

    VECTOR_ENHANCE_CACHE_PREFIX: str = "cache:vector:enhance:"
    """向量检索 ANN 结果的缓存 key 前缀，运行时拼接查询文本与 fetch_k 的 hash"""

    GRAPH_SIGNAL_CACHE_PREFIX: str = "cache:graph:signal:"
    """图谱增强个性化信号的缓存 key 前缀，运行时拼接信号名、文章 id 与用户 id"""

    GRAPH_CANDIDATE_CACHE_PREFIX: str = "cache:graph:candidate:"
    """候选间相似标签信号的缓存 key 前缀，运行时拼接候选集合的 hash"""

    # ===== 同步时间 key =====

    VECTOR_SYNC_TIME: str = "vector_sync:last_sync_time"
    """向量同步最近一次完成时间的缓存 key"""

    NEO4J_SYNC_TIME: str = "neo4j_sync:last_sync_time"
    """图谱同步最近一次完成时间的缓存 key"""

    # ===== 文章内容 hash（前缀 + 运行时拼接 article_id）=====

    ARTICLE_CONTENT_HASH_PREFIX: str = "article_content_hash:"
    """文章内容 hash 的 key 前缀，运行时拼接 article_id"""

    # ===== 分布式锁 key 及其过期时间（集中于此，消除 messages/defaults 重复定义）=====

    LOCK_TASK_ANALYZE_CACHE: str = "lock:task:analyze:cache"
    """分析缓存刷新任务的分布式锁 key"""

    LOCK_TASK_ANALYZE_CACHE_EXPIRE: int = 600
    """分析缓存刷新锁的过期秒数"""

    LOCK_TASK_NEO4J_SYNC: str = "lock:task:neo4j:sync"
    """图谱同步任务的分布式锁 key"""

    LOCK_TASK_NEO4J_SYNC_EXPIRE: int = 3600
    """图谱同步锁的过期秒数"""

    LOCK_TASK_VECTOR_SYNC: str = "lock:task:vector:sync"
    """向量同步任务的分布式锁 key"""

    LOCK_TASK_VECTOR_SYNC_EXPIRE: int = 86400
    """向量同步锁的过期秒数"""

    LOCK_TASK_WAREHOUSE: str = "lock:task:warehouse"
    """数仓同步任务的分布式锁 key"""

    LOCK_TASK_WAREHOUSE_EXPIRE: int = 600
    """数仓同步锁的过期秒数"""
