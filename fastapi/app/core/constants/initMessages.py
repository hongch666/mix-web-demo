class InitMessages:
    """
    启动/初始化消息类 — DeepSeek/Gemini/GPT 初始化日志
    """

    DEEPSEEK_INIT_LOG: str = "DeepSeek 客户端初始化完成"
    GEMINI_INIT_LOG: str = "Gemini 客户端初始化完成"
    GPT_INIT_LOG: str = "GPT 客户端初始化完成"
    STARTUP_MESSAGE: str = "FastAPI服务启动成功"
    INIT_IP: str = "127.0.0.1"
    HTTP_CLIENT_POOL_INITIALIZED: str = "HTTP 客户端连接池已创建"
    HTTP_CLIENT_POOL_CLOSED: str = "HTTP 客户端连接池已关闭"
    SCHEDULER_STARTED: str = "定时任务调度器已启动"
    SCHEDULER_VECTOR_SYNC_MESSAGE: str = "  - 向量同步任务：每 24 小时执行一次"
    SCHEDULER_ANALYZE_CACHE_UPDATE_MESSAGE: str = "  - 分析接口缓存更新任务：每 10 分钟执行一次（启动时立即执行）"
    SCHEDULER_NEO4J_SYNC_MESSAGE: str = "  - Neo4j 知识图谱同步任务：每 24 小时执行一次（启动时立即执行）"
