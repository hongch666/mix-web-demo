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
