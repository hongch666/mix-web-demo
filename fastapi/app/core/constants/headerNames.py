class HeaderNames:
    """网关与微服务间透传的请求头名称常量"""

    # ===== 请求头名称 =====

    USER_ID: str = "X-User-Id"
    """网关透传的用户 ID 请求头"""
    USERNAME: str = "X-Username"
    """网关透传的用户名请求头"""
    SESSION_ID: str = "X-Session-Id"
    """网关透传的会话 ID 请求头"""
    AUTHORIZATION: str = "Authorization"
    """访问令牌请求头"""
    INTERNAL_TOKEN: str = "X-Internal-Token"
    """服务间内部令牌请求头"""
    BEARER_PREFIX: str = "Bearer "
    """访问令牌与内部令牌取值使用的 Bearer 前缀"""
