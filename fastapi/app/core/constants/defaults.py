class Defaults:
    """
    配置默认值类 — TTL、权重、超时
    """

    # ===== 缓存 =====
    CACHE_L1_TTL: int = 300
    CACHE_L2_TTL: int = 600

    # ===== 分布式锁 =====
    LOCK_DEFAULT_EXPIRE: int = 30

    # ===== 权限 =====
    ROLE_ADMIN: str = "admin"
    ROLE_USER: str = "user"
