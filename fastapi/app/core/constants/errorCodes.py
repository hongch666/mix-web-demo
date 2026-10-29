class ErrorCodes:
    """
    错误标识类 — 传给 BusinessException 的 error 参数
    """

    # ===== 400 Bad Request =====

    ERROR_PARAM_PARSE_FAILED: str = "PARAM_PARSE_FAILED"
    """请求参数解析失败"""
    ERROR_COLLECTION_NAME_REQUIRED: str = "COLLECTION_NAME_REQUIRED"
    """MongoDB 工具缺少 collection_name 参数"""
    ERROR_USER_SCOPE_TARGET_MISSING: str = "USER_SCOPE_TARGET_MISSING"
    """用户范围校验缺少目标用户 ID"""

    # ===== 401 Unauthorized =====

    ERROR_USER_NOT_LOGIN: str = "USER_NOT_LOGIN"
    """未登录"""
    ERROR_INTERNAL_TOKEN_MISSING: str = "INTERNAL_TOKEN_MISSING"
    """缺少内部服务令牌请求头"""
    ERROR_INTERNAL_TOKEN_INVALID: str = "INTERNAL_TOKEN_INVALID"
    """内部服务令牌无效"""
    ERROR_INTERNAL_TOKEN_EXPIRED: str = "INTERNAL_TOKEN_EXPIRED"
    """内部服务令牌已过期"""

    # ===== 403 Forbidden =====

    ERROR_PERMISSION_CHECK_FAILED: str = "PERMISSION_CHECK_FAILED"
    """权限校验失败"""
    ERROR_NO_ADMIN_PERMISSION: str = "NO_ADMIN_PERMISSION"
    """缺少管理员权限"""
    ERROR_USER_NO_ADMIN_PERMISSION: str = "USER_NO_ADMIN_PERMISSION"
    """当前用户不是管理员"""
    ERROR_INTENT_ROUTER_NO_PERMISSION: str = "INTENT_ROUTER_NO_PERMISSION"
    """意图路由判定为无权限"""
    ERROR_INTERNAL_TOKEN_SERVICE_MISMATCH: str = "INTERNAL_TOKEN_SERVICE_MISMATCH"
    """内部令牌的服务名与期望不符"""
    ERROR_USER_SCOPE_FORBIDDEN: str = "USER_SCOPE_FORBIDDEN"
    """越权访问其他用户的数据"""

    # ===== 404 Not Found =====

    ERROR_USER_NOT_FOUND: str = "USER_NOT_FOUND"
    """用户不存在"""
    ERROR_ARTICLE_NOT_FOUND: str = "ARTICLE_NOT_FOUND"
    """文章不存在"""
    ERROR_NO_RELEVANT_ARTICLES: str = "NO_RELEVANT_ARTICLES"
    """检索不到相关文章"""
    ERROR_AI_CHAT_NO_INSTANCE: str = "AI_CHAT_NO_INSTANCE"
    """没有可用的 AI 对话实例"""

    # ===== 429 Too Many Requests =====

    ERROR_GEMINI_QUOTA_EXCEEDED: str = "GEMINI_QUOTA_EXCEEDED"
    """Gemini 接口配额用尽"""
    ERROR_GEMINI_RATE_LIMIT_EXCEEDED: str = "GEMINI_RATE_LIMIT_EXCEEDED"
    """Gemini 接口调用频率超限"""
    ERROR_GPT_RATE_LIMIT_EXCEEDED: str = "GPT_RATE_LIMIT_EXCEEDED"
    """GPT 接口调用频率超限"""

    # ===== 500 Internal Server Error =====

    ERROR_FASTAPI_SERVER_ERROR: str = "FASTAPI_SERVER_ERROR"
    """FastAPI 服务内部错误"""
    ERROR_GLM_CALL_FAILED: str = "GLM_CALL_FAILED"
    """GLM 调用失败"""
    ERROR_GEMINI_CALL_FAILED: str = "GEMINI_CALL_FAILED"
    """Gemini 调用失败"""
    ERROR_GPT_CALL_FAILED: str = "GPT_CALL_FAILED"
    """GPT 调用失败"""
    ERROR_SERVICE_CALL_FAILED: str = "SERVICE_CALL_FAILED"
    """下游服务调用失败"""
    ERROR_INTERNAL_TOKEN_SECRET_NOT_NULL: str = "INTERNAL_TOKEN_SECRET_NOT_NULL"
    """内部令牌密钥未配置"""

    # ===== 503 Service Unavailable =====

    ERROR_RABBITMQ_CLIENT_NOT_INITIALIZED: str = "RABBITMQ_CLIENT_NOT_INITIALIZED"
    """RabbitMQ 客户端未初始化"""
    ERROR_RABBITMQ_NOT_CONNECTED: str = "RABBITMQ_NOT_CONNECTED"
    """RabbitMQ 未连接"""
