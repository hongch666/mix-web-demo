class Messages:
    """
    消息类常量 — 日志消息、用户提示、RabbitMQ/Redis/Nacos 消息
    """

    # ===== 内部令牌 =====
    INTERNAL_TOKEN_SECRET_NOT_NULL: str = "内部令牌密钥未配置"
    INTERNAL_TOKEN_MISSING: str = "请求头中缺少内部令牌"
    INTERNAL_TOKEN_INVALID: str = "内部令牌无效"
    INTERNAL_TOKEN_EXPIRED: str = "内部令牌已过期"
    SERVICE_NAME_MISMATCH: str = "服务名称不匹配"

    # ===== 测试/启动 =====
    TEST_MESSAGE: str = "Hello, I am FastAPI!"
    STARTUP_MESSAGE: str = "FastAPI服务启动成功"

    # ===== AI评论 =====
    AI_COMMENT_TASK_SUBMITTED: str = "AI生成评论任务已提交"
    AI_COMMENT_WITH_REFERENCE_TASK_SUBMITTED: str = (
        "基于权威参考文本的AI生成评论任务已提交"
    )

    # ===== 缓存 =====
    CACHE_HIT_L1: str = "L1缓存命中"
    CACHE_HIT_L2: str = "L2缓存命中"
    CACHE_MISS: str = "L1/L2缓存均未命中，从数据源查询"
    CACHE_SET_L1: str = "设置L1缓存"
    CACHE_SET_L2: str = "设置L2缓存"

    # ===== RabbitMQ =====
    RABBITMQ_CONNECTED_MESSAGE: str = "RabbitMQ 连接已建立"
    RABBITMQ_CLIENT_NOT_INITIALIZED_MESSAGE: str = "RabbitMQ 客户端未初始化"
    RABBITMQ_CONNECTION_CLOSED_MESSAGE: str = "RabbitMQ 连接已关闭"
    RABBITMQ_SEND_TO_QUEUE_SUCCESS: str = "RabbitMQ 消息已发送到队列"
    RABBITMQ_SEND_TO_QUEUE_FAILURE: str = "RabbitMQ 发送消息到队列失败"
    RABBITMQ_NOT_AVAILABLE: str = "日志装饰器捕获到异常，请检查日志详情"
    API_RABBITMQ_LOGGING_SUCCESS: str = "API 日志已发送到队列"
    API_RABBITMQ_LOGGING_FAILURE: str = "API 日志发送到队列失败"

    # ===== Redis =====
    REDIS_INITIALIZED_MESSAGE: str = "Redis 客户端初始化成功"
    REDIS_GET_FAILED: str = "Redis GET 失败"
    REDIS_SET_FAILED: str = "Redis SET 失败"
    REDIS_DELETE_FAILED: str = "Redis DELETE 失败"

    # ===== Nacos =====
    NACOS_REGISTER_SUCCESS: str = "注册到 nacos 成功"
    NACOS_REGISTER_DEV_MODE_MESSAGE: str = (
        "SERVER_MODE=dev，Nacos 注册统一使用 127.0.0.1"
    )

    # ===== 异常处理 =====
    EXCEPTION_HANDLER_MESSAGE: str = "FastAPI服务器错误"

    # ===== 分布式锁 =====
    REDIS_LOCK_ACQUIRE_SUCCESS: str = "获取分布式锁成功"
    REDIS_LOCK_ACQUIRE_FAIL: str = "获取分布式锁失败"
    REDIS_LOCK_RELEASE_SUCCESS: str = "释放分布式锁成功"
    REDIS_LOCK_RELEASE_FAIL: str = "释放分布式锁失败"

    # ===== 调度器 =====
    SCHEDULER_STARTED: str = "定时任务调度器已启动"

    # ===== 服务降级 =====
    UNKNOWN_ERROR: str = "未知错误"
    CIRCUIT_BREAKER_OPEN: str = "熔断器已开启"
    AI_CHAT_NO_INSTANCE_MESSAGE: str = "找不到可用的服务实例"

    # ===== 向量搜索 =====
    VECTOR_SEARCH_SIMILARITY_REASON: str = "语义内容高度相关"
    VECTOR_ENHANCE_DEGRADE_LOG: str = "向量增强失败"

    # ===== 图谱搜索 =====
    GRAPH_SEARCH_QUERY_SUCCESS: str = "图谱查询成功"
    GRAPH_SEARCH_QUERY_FAILURE: str = "图谱查询失败"

    # ===== Agent =====
    EMBEDDING_CONFIG_INCOMPLETE_MESSAGE: str = "Embedding配置不完整"
    RAG_SERVICE_NOT_INITIALIZED_MESSAGE: str = "RAG服务未初始化"
    NEO4J_SERVICE_UNAVAILABLE_MESSAGE: str = "Neo4j 知识图谱服务暂不可用"
    NEO4J_CONFIG_NOT_INITIALIZED_MESSAGE: str = "Neo4j 连接参数未初始化"
    NEO4J_QUERY_TOOLS_INITIALIZED_MESSAGE: str = "Neo4j 查询工具初始化成功"
    NEO4J_NO_RESULT_MESSAGE: str = "未找到相关知识图谱结果"
    NEO4J_QUERY_EMPTY_MESSAGE: str = "查询未返回结果"
    NEO4J_READ_ONLY_LIMIT_MESSAGE: str = (
        "安全限制：Neo4j 工具只允许执行单条只读 Cypher 查询"
    )
