class HttpCode:
    """HTTP 状态码常量 - 与 HTTP 响应状态码一致，同时作为响应体中的 code 字段值"""

    # ===== HTTP 状态码 =====

    OK: int = 200
    """请求成功"""
    BAD_REQUEST: int = 400
    """参数或请求体不合法"""
    UNAUTHORIZED: int = 401
    """未认证或令牌失效"""
    FORBIDDEN: int = 403
    """已认证但无权限"""
    NOT_FOUND: int = 404
    """资源不存在"""
    CONFLICT: int = 409
    """资源状态冲突"""
    UNPROCESSABLE_ENTITY: int = 422
    """参数语义校验不通过"""
    TOO_MANY_REQUESTS: int = 429
    """触发频率限流"""
    INTERNAL_SERVER_ERROR: int = 500
    """服务内部异常"""
    BAD_GATEWAY: int = 502
    """下游服务返回异常"""
    SERVICE_UNAVAILABLE: int = 503
    """依赖缺失导致服务不可用"""
    GATEWAY_TIMEOUT: int = 504
    """下游调用超时"""
