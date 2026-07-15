from typing import List


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
    UPDATE_ANALYZE_CACHES_ANALYZE_SERVICE_NONE_MESSAGE: str = "update_analyze_caches: analyze_service 为 None，跳过缓存更新"
    UPDATE_ANALYZE_CACHES_START_MESSAGE: str = "开始更新分析接口缓存"
    UPDATE_ANALYZE_CACHES_TOP10_START_MESSAGE: str = "更新前10篇文章缓存..."
    UPDATE_ANALYZE_CACHES_TOP10_SUCCESS_MESSAGE: str = "前10篇文章缓存更新成功"
    UPDATE_ANALYZE_CACHES_WORDCLOUD_START_MESSAGE: str = "更新词云图缓存..."
    UPDATE_ANALYZE_CACHES_WORDCLOUD_SUCCESS_MESSAGE: str = "词云图缓存更新成功"
    UPDATE_ANALYZE_CACHES_STATISTICS_START_MESSAGE: str = "更新文章统计信息缓存..."
    UPDATE_ANALYZE_CACHES_STATISTICS_SUCCESS_MESSAGE: str = "文章统计信息缓存更新成功"
    UPDATE_ANALYZE_CACHES_CATEGORY_STATISTICS_START_MESSAGE: str = "更新按分类统计文章数量缓存..."
    UPDATE_ANALYZE_CACHES_CATEGORY_STATISTICS_SUCCESS_MESSAGE: str = "按分类统计文章数量缓存更新成功"
    UPDATE_ANALYZE_CACHES_MONTHLY_STATISTICS_START_MESSAGE: str = "更新月度文章发布统计缓存..."
    UPDATE_ANALYZE_CACHES_MONTHLY_STATISTICS_SUCCESS_MESSAGE: str = "月度文章发布统计缓存更新成功"
    UPDATE_ANALYZE_CACHES_COMPLETE_MESSAGE: str = "分析接口缓存更新完成"


    AGENT_PARSING_ERROR_HINT: str = (
        "上一轮回复格式不正确，请严格按以下格式输出，并且不要输出多余内容：\n"
        "Thought: 先思考\n"
        "Action: 从工具列表中选择一个工具名\n"
        "Action Input: 工具输入\n"
        "如果已经有最终答案，再输出：\n"
        "Final Answer: 最终回答"
    )

    AGENT_PROCESSING_MESSAGE: str = (
        "使用Agent处理，可同时调用SQL、RAG和Neo4j知识图谱工具"
    )

    AGENT_START_PROCESSING_MESSAGE: str = "Agent开始处理..."

    AGENT_START_STREAMING_MESSAGE: str = "Agent思考完成,开始流式输出优化后的答案"

    AIO_PKA_EVENT_LOOP_ERROR: str = "检测到运行中的事件循环，跳过 RabbitMQ 同步关闭"

    AI_CHAT_SQL_TABLE_EXISTENCE_CHECK: str = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'ai_history'"

    AI_CHAT_TABLE_CREATION_MESSAGE: str = "ai_history 表创建完成"

    AI_CHAT_TABLE_EXISTS_MESSAGE: str = "ai_history 表已存在"

    AI_CHAT_TABLE_UNSUPPORTED_MESSAGE: str = "仅支持创建 ai_history 表"

    APILOG_ASYNC_ERROR: str = "apiLog 装饰器只支持异步函数"

    ARTICLE_MAPPER_METHOD_MISSING_ERROR: str = "ArticleMapper 未提供获取文章的方法"

    ARTICLE_NOT_EXISTS_ERROR: str = "文章不存在"

    ASYNC_SYNC_CALL_IN_EVENT_LOOP_ERROR: str = (
        "同步方法不能在运行中的事件循环里直接调用"
    )

    BLOCKED_KEYWORDS: List[str] = [
        "CREATE",
        "MERGE",
        "SET",
        "DELETE",
        "DETACH",
        "REMOVE",
        "DROP",
        "LOAD CSV",
        "CALL APOC",
    ]

    CATEGORY_NO_AUTHORITATIVE_REFERENCE_TEXT_ERROR: str = (
        "该分类暂无权威参考文本，请根据您的专业知识进行评价。"
    )

    CATEGORY_STATISTICS_CACHE_FETCH_FAILED: str = (
        "get_category_article_count_service: [缓存未命中] 开始查询数据源"
    )

    CATEGORY_STATISTICS_CLICKHOUSE_GET: str = "从ClickHouse获取分类文章统计"

    CATEGORY_STATISTICS_CLICKHOUSE_QUERY: str = "从ClickHouse查询分类文章统计数据"

    CATEGORY_STATISTICS_DB_SOURCE: str = (
        "get_category_article_count_service: 使用 DB 数据源"
    )

    CHAT_SYSTEM_MESSAGE: str = (
        "你是一个中文AI助手，用于提供文章和博客推荐及分析系统数据。"
    )

    CLICKHOUSE_CACHE_MISS_QUERY_MESSAGE: str = "ClickHouse缓存未命中，将查询数据源"

    CLICKHOUSE_CONNECTION_POOL_CLOSED_MESSAGE: str = "[ClickHouse连接池] 所有连接已关闭"

    CLICKHOUSE_CONNECTION_POOL_FULL_MESSAGE: str = (
        "[ClickHouse连接池] 连接池已满，连接已关闭"
    )

    COLLECTION_NAME_VALIDATION_ERROR: str = "错误: 必须提供 collection_name 参数"

    CONCURRENT_CHAT_MESSAGE_SUCCESS: str = "权威文章生成完成，所有大模型总结已完成"

    CONCURRENT_SUMMARY_MESSAGE: str = "开始并发调用三个大模型进行总结"

    DANGEROUS_SQL_REQUEST_PATTERNS: List[str] = [
        r"\b(update|delete|insert|drop|alter|truncate|create|replace|merge)\b",
        r"(把|将).*(修改|更新|删除|新增|插入|写入|创建|清空|重置|下架|发布|设为|设置为|改成|改为)",
        r"(帮我|请|给我|直接|批量).*(修改|更新|删除|新增|插入|写入|创建|清空|重置|下架|发布|设为|设置为|改成|改为).*(数据库|数据|表|记录|文章|用户|评论|点赞|收藏|status|状态|字段)",
        r"(修改|更新|删除|新增|插入|写入|创建|清空|重置).*(数据库|数据|表|记录|文章|用户|评论|点赞|收藏|status|状态|字段)",
        r"(删除|清空|重置).*(数据|记录|表|文章|用户|评论)",
        r"(新增|插入|写入|创建).*(数据|记录|表|文章|用户|评论)",
    ]

    DB_CACHE_MISS_QUERY_DB_MESSAGE: str = "[缓存] L1/L2 都未命中，需要查询 DB"

    DEEPSEEK_AGENT_INITIALIZATION_SUCCESS: str = "DeepSeek Agent服务初始化完成"

    DEEPSEEK_CALL_FAILED_ERROR: str = "DeepSeek调用失败"

    DEEPSEEK_CONFIGURATION_INCOMPLETE_ERROR: str = "DeepSeek配置不完整，客户端未初始化"

    DEFAULT_KEYWORDS: str = [
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

    ERROR_AI_CHAT_NO_INSTANCE: str = "AI_CHAT_NO_INSTANCE"

    ERROR_ARTICLE_NOT_FOUND: str = "ARTICLE_NOT_FOUND"

    ERROR_COLLECTION_NAME_REQUIRED: str = "COLLECTION_NAME_REQUIRED"

    ERROR_DEEPSEEK_CALL_FAILED: str = "DEEPSEEK_CALL_FAILED"

    ERROR_DEEPSEEK_NOT_CONFIGURED: str = "DEEPSEEK_NOT_CONFIGURED"

    ERROR_FASTAPI_SERVER_ERROR: str = "FASTAPI_SERVER_ERROR"

    ERROR_GEMINI_CALL_FAILED: str = "GEMINI_CALL_FAILED"

    ERROR_GEMINI_NOT_CONFIGURED: str = "GEMINI_NOT_CONFIGURED"

    ERROR_GEMINI_QUOTA_EXCEEDED: str = "GEMINI_QUOTA_EXCEEDED"

    ERROR_GEMINI_RATE_LIMIT_EXCEEDED: str = "GEMINI_RATE_LIMIT_EXCEEDED"

    ERROR_GPT_CALL_FAILED: str = "GPT_CALL_FAILED"

    ERROR_GPT_NOT_CONFIGURED: str = "GPT_NOT_CONFIGURED"

    ERROR_GPT_RATE_LIMIT_EXCEEDED: str = "GPT_RATE_LIMIT_EXCEEDED"

    ERROR_INITIALIZATION_ERROR: str = "INITIALIZATION_ERROR"

    ERROR_INTENT_ROUTER_NO_PERMISSION: str = "INTENT_ROUTER_NO_PERMISSION"

    ERROR_INTERNAL_TOKEN_EXPIRED: str = "INTERNAL_TOKEN_EXPIRED"

    ERROR_INTERNAL_TOKEN_INVALID: str = "INTERNAL_TOKEN_INVALID"

    ERROR_INTERNAL_TOKEN_MISSING: str = "INTERNAL_TOKEN_MISSING"

    ERROR_INTERNAL_TOKEN_SECRET_NOT_NULL: str = "INTERNAL_TOKEN_SECRET_NOT_NULL"

    ERROR_INTERNAL_TOKEN_SERVICE_MISMATCH: str = "INTERNAL_TOKEN_SERVICE_MISMATCH"

    ERROR_NO_ADMIN_PERMISSION: str = "NO_ADMIN_PERMISSION"

    ERROR_NO_AVAILABLE_SERVICE_INSTANCE: str = "NO_AVAILABLE_SERVICE_INSTANCE"

    ERROR_NO_RELEVANT_ARTICLES: str = "NO_RELEVANT_ARTICLES"

    ERROR_OSS_CLIENT_NOT_INITIALIZED: str = "OSS_CLIENT_NOT_INITIALIZED"

    ERROR_OSS_PUT_TIMEOUT: str = "OSS_PUT_TIMEOUT"

    ERROR_PARAM_PARSE_FAILED: str = "PARAM_PARSE_FAILED"

    ERROR_PERMISSION_CHECK_FAILED: str = "PERMISSION_CHECK_FAILED"

    ERROR_RABBITMQ_CLIENT_NOT_INITIALIZED: str = "RABBITMQ_CLIENT_NOT_INITIALIZED"

    ERROR_RABBITMQ_CONFIG_NOT_FOUND: str = "RABBITMQ_CONFIG_NOT_FOUND"

    ERROR_RABBITMQ_NOT_CONNECTED: str = "RABBITMQ_NOT_CONNECTED"

    ERROR_REQUEST_TIMEOUT: str = "REQUEST_TIMEOUT"

    ERROR_SERVICE_CALL_FAILED: str = "SERVICE_CALL_FAILED"

    ERROR_SERVICE_DISCOVERY_FAILED: str = "SERVICE_DISCOVERY_FAILED"

    ERROR_USER_NOT_FOUND: str = "USER_NOT_FOUND"

    ERROR_USER_NOT_LOGIN: str = "USER_NOT_LOGIN"

    ERROR_USER_NO_ADMIN_PERMISSION: str = "USER_NO_ADMIN_PERMISSION"

    EXPORT_ARTICLES_EXCEL_FILENAME: str = "articles.xlsx"

    EXPORT_ARTICLES_EXCEL_TIP: str = "文章表（本表导出自系统，包含所有文章数据）"

    FIRST_TIME_SYNC_MESSAGE: str = "首次同步向量库，将同步所有已发布文章"

    GEMINI_AGENT_INITIALIZATION_SUCCESS: str = "Gemini Agent服务初始化完成"

    GEMINI_CALL_FAILED_ERROR: str = "Gemini调用失败"

    GEMINI_CONFIGURATION_INCOMPLETE_ERROR: str = "Gemini配置不完整，客户端未初始化"

    GEMINI_INVALID_API_KEY_ERROR: str = "API密钥无效。请检查Gemini API密钥配置。"

    GEMINI_QUOTA_EXCEEDED_ERROR: str = "Gemini API 配额已用完。请稍后重试。"

    GEMINI_RATE_LIMIT_EXCEEDED_ERROR: str = "Gemini API调用频率超限。请稍后重试。"

    GENERIC_CHAT_MESSAGE: str = (
        "你是一个中文AI助手，用于提供文章和博客推荐及分析系统数据。"
    )

    GET_TOP_FAIL: str = "获取文章浏览分布失败"

    GPT_AGENT_INITIALIZATION_SUCCESS: str = "GPT Agent服务初始化完成"

    GPT_CALL_FAILED_ERROR: str = "GPT调用失败"

    GPT_CONFIGURATION_INCOMPLETE_ERROR: str = "GPT配置不完整，客户端未初始化"

    GPT_INVALID_API_KEY_ERROR: str = "API密钥无效。请检查GPT API密钥配置。"

    GPT_QUOTA_EXCEEDED_ERROR: str = "GPT API 配额已用完。请稍后重试。"

    GPT_RATE_LIMIT_EXCEEDED_ERROR: str = "GPT API调用频率超限。请稍后重试。"

    GRAPH_SEARCH_NEO4J_EXCEPTION_LOG: str = "Neo4j 查询异常: {}"

    GRAPH_SEARCH_PATH_CANDIDATE: str = "Article-TAGGED_AS-Tag-TAGGED_AS-Article"

    GRAPH_SEARCH_PATH_FOLLOWED: str = "User-FOLLOWS-User-PUBLISHED_BY-Article"

    GRAPH_SEARCH_PATH_INTEREST: str = "User-LIKES-Article-TAGGED_AS-Tag"

    GRAPH_SEARCH_PATH_KEYWORD: str = "Article-TAGGED_AS-Tag"

    GRAPH_SEARCH_PATH_SUB_CATEGORY: str = (
        "User-LIKES|COLLECTS|COMMENTED_ON-Article-BELONGS_TO-SubCategory"
    )

    GRAPH_SEARCH_QUERY_EXCEPTION_LOG: str = "图谱信号查询异常: {}"

    GRAPH_SEARCH_REASON_CANDIDATE: str = "与当前搜索结果中的多篇文章标签相关"

    GRAPH_SEARCH_REASON_FOLLOWED: str = "来自你关注的作者"

    GRAPH_SEARCH_REASON_INTEREST: str = "命中兴趣标签"

    GRAPH_SEARCH_REASON_KEYWORD: str = "命中图谱标签"

    GRAPH_SEARCH_REASON_SUB_CATEGORY: str = "属于你常看的分类"

    HTTP_CLIENT_POOL_CLOSED: str = "httpx 共享连接池已关闭"

    HTTP_CLIENT_POOL_INITIALIZED: str = "httpx 共享连接池已初始化"

    INITIALIZATION_ERROR: str = "聊天服务未配置或初始化失败"

    INIT_IP: str = "127.0.0.1"

    INTENT_ROUTER_NO_PERMISSION_ERROR: str = "权限拒绝：此功能需要登录后才能使用。请先登录您的账户。您可以继续使用文章搜索和闲聊功能。"

    KEYWORDS_EMPTY: str = "关键词字典为空，无法生成词云图"

    L1_CACHE_CLEARED: str = "[L1缓存] 已清除"

    L1_CACHE_TTL_EXPIRED: str = "[L1缓存] TTL过期"

    L1_CACHE_UPDATED: str = "[L1缓存] 已更新"

    L2_CACHE_CLEARED: str = "[L2缓存] Redis 已清除"

    L2_CACHE_HIT: str = "[L2缓存] 命中 Redis"

    L2_CACHE_MISS: str = "[L2缓存] Redis 未命中"

    L2_CACHE_UNAVAILABLE: str = "[L2缓存] Redis 不可用"

    LOCK_TASK_ANALYZE_CACHE: str = "lock:task:analyze:cache"

    LOCK_TASK_ANALYZE_CACHE_EXPIRE: int = 600

    LOCK_TASK_NEO4J_SYNC: str = "lock:task:neo4j:sync"

    LOCK_TASK_NEO4J_SYNC_EXPIRE: int = 3600

    LOCK_TASK_VECTOR_SYNC: str = "lock:task:vector:sync"

    LOCK_TASK_VECTOR_SYNC_EXPIRE: int = 86400

    MESSAGE_RETRIEVAL_ERROR: str = "无法获取结果"

    MONGODB_COLLECTION_NAME_INPUT_DESC: str = "collection 的名称"

    MONGODB_FILTER_INPUT_DESC: str = "MongoDB 查询条件"

    MONGODB_LIMIT_INPUT_DESC: str = "返回结果数量限制"

    MONGODB_LIST_COLLECTIONS_TOOL_NAME: str = "list_mongodb_collections"

    MONGODB_QUERY_TOOL_NAME: str = "query_mongodb"

    MONTHLY_STATISTICS_CACHE_FETCH_FAILED: str = (
        "get_monthly_publish_count_service: [缓存未命中] 开始查询数据源"
    )

    MONTHLY_STATISTICS_CLICKHOUSE_GET: str = "从ClickHouse获取月度发布统计"

    MONTHLY_STATISTICS_CLICKHOUSE_QUERY: str = "从ClickHouse查询月度发布统计数据"

    MONTHLY_STATISTICS_DB_SOURCE: str = (
        "get_monthly_publish_count_service: 使用 DB 数据源"
    )

    NACOS_INITIALIZATION_FAILED: str = "nacos 初始化不可用"

    NEO4J_CLEANUP_DELETED_DATA_START_MESSAGE: str = (
        "[知识图谱] 开始清理 Neo4j 中已删除的 MySQL 数据"
    )

    NEO4J_CLEANUP_LABEL_ARTICLE: str = "失效文章节点"

    NEO4J_CLEANUP_LABEL_ARTICLE_SUB_CATEGORY_RELATION: str = "失效文章子分类关系"

    NEO4J_CLEANUP_LABEL_CATEGORY: str = "失效主分类节点"

    NEO4J_CLEANUP_LABEL_COLLECT_RELATION: str = "失效收藏关系"

    NEO4J_CLEANUP_LABEL_COMMENT_RELATION: str = "失效评论关系"

    NEO4J_CLEANUP_LABEL_FOLLOW_RELATION: str = "失效关注关系"

    NEO4J_CLEANUP_LABEL_LIKE_RELATION: str = "失效点赞关系"

    NEO4J_CLEANUP_LABEL_PUBLISHED_BY_RELATION: str = "失效文章作者关系"

    NEO4J_CLEANUP_LABEL_SUB_CATEGORY: str = "失效子分类节点"

    NEO4J_CLEANUP_LABEL_SUB_CATEGORY_CATEGORY_RELATION: str = "失效子分类主分类关系"

    NEO4J_CLEANUP_LABEL_TAG: str = "失效标签节点"

    NEO4J_CLEANUP_LABEL_TAGGED_AS_RELATION: str = "失效文章标签关系"

    NEO4J_CLEANUP_LABEL_USER: str = "失效用户节点"

    NEO4J_CREATE_CONSTRAINTS: List[str] = [
        "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
        "CREATE CONSTRAINT category_id_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT sub_category_id_unique IF NOT EXISTS FOR (s:SubCategory) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT article_id_unique IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE",
        "CREATE CONSTRAINT tag_name_unique IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE",
    ]

    NEO4J_CURRENT_LOOP_DRIVER_CLOSED_MESSAGE: str = "Neo4j 当前事件循环驱动已关闭"

    NEO4J_CUSTOM_CYPHER_INPUT_DESC: str = "只读 Cypher 查询语句"

    NEO4J_CUSTOM_CYPHER_TOOL_NAME: str = "execute_custom_cypher_query"

    NEO4J_DRIVER_CLOSED_MESSAGE: str = "Neo4j 驱动已关闭"

    NEO4J_DRIVER_NOT_INITIALIZED_MESSAGE: str = "Neo4j 驱动未初始化，无法创建会话"

    NEO4J_GRAPH_COUNT_CYPHER: str = "MATCH (n) RETURN count(n) AS total LIMIT 1"

    NEO4J_GRAPH_EMPTY_FULL_SYNC_MESSAGE: str = "Neo4j 当前无图谱数据，切换为全量同步"

    NEO4J_INCREMENTAL_SYNC_START_MESSAGE: str = "[知识图谱] 开始增量同步 MySQL 到 Neo4j"

    NEO4J_LABEL_ARTICLE: str = "文章"

    NEO4J_LABEL_ARTICLE_AUTHOR_RELATION: str = "文章-作者关系"

    NEO4J_LABEL_ARTICLE_SUB_CATEGORY_RELATION: str = "文章-子分类关系"

    NEO4J_LABEL_ARTICLE_TAG_RELATION: str = "文章-标签关系"

    NEO4J_LABEL_CATEGORY: str = "主分类"

    NEO4J_LABEL_COLLECT_RELATION: str = "收藏关系"

    NEO4J_LABEL_COMMENT_RELATION: str = "评论关系"

    NEO4J_LABEL_FOLLOW_RELATION: str = "关注关系"

    NEO4J_LABEL_LIKE_RELATION: str = "点赞关系"

    NEO4J_LABEL_SUB_CATEGORY: str = "子分类"

    NEO4J_LABEL_SUB_CATEGORY_RELATION: str = "子分类-主分类关系"

    NEO4J_LABEL_TAG: str = "标签"

    NEO4J_LABEL_USER: str = "用户"

    NEO4J_LOOP_NOT_RUNNING_MESSAGE: str = (
        "当前没有运行中的事件循环，无法创建 Neo4j 异步驱动"
    )

    NEO4J_NO_INCREMENTAL_DATA_MESSAGE: str = "没有检测到需要同步的 Neo4j 增量数据"

    NEO4J_PREDEFINED_QUERY_TOOL_NAME: str = "execute_knowledge_graph_query"

    NEO4J_QUERY_NAME_INPUT_DESC: str = "预定义查询名称，可选值: "

    NEO4J_QUERY_PARAMS_INPUT_DESC: str = (
        '查询参数，例如 {"id": 1, "name": "人工智能", "limit": 10}'
    )

    NEO4J_SQL_INCREMENTAL_SUFFIX_FORMAT: str = "%s WHERE %s >= '%s' ORDER BY %s ASC"

    NEO4J_SQL_SELECT_ARTICLES: str = (
        "SELECT id, title, tags, status, views, user_id, sub_category_id, "
        "create_at, update_at, content FROM articles"
    )

    NEO4J_SQL_SELECT_CATEGORIES: str = "SELECT id, name, update_time FROM category"

    NEO4J_SQL_SELECT_COLLECTS: str = (
        "SELECT user_id, article_id, created_time FROM collects"
    )

    NEO4J_SQL_SELECT_COMMENTS: str = (
        "SELECT id, user_id, article_id, create_time, update_time FROM comments"
    )

    NEO4J_SQL_SELECT_FOCUS: str = "SELECT user_id, focus_id, created_time FROM focus"

    NEO4J_SQL_SELECT_LIKES: str = "SELECT user_id, article_id, created_time FROM likes"

    NEO4J_SQL_SELECT_SUB_CATEGORIES: str = (
        "SELECT id, name, category_id, update_time FROM sub_category"
    )

    NEO4J_SQL_SELECT_USERS: str = (
        "SELECT id, name, email, role, img, signature, create_at, update_at FROM user"
    )

    NEO4J_SYNC_START_MESSAGE: str = "[知识图谱] 开始全量同步 MySQL 到 Neo4j"

    NEO4J_TASK_FINISH_MESSAGE: str = "[知识图谱任务] MySQL 到 Neo4j 同步完成: %s"

    NEO4J_TASK_START_MESSAGE: str = "[知识图谱任务] 开始执行 MySQL 到 Neo4j 全量同步"

    NO_ARTICLES_DATA_MESSAGE: str = "没有文章数据"

    NO_CHANGED_ARTICLES_MESSAGE: str = "没有文章内容变更，跳过向量库同步"

    NO_PERMISSION_ERROR: str = "您没有权限访问此功能，请联系管理员开通相关权限。"

    NO_PUBLISHED_ARTICLES_MESSAGE: str = "没有已发布的文章需要同步"

    NO_RELEVANT_ARTICLES_FOUND_MESSAGE: str = "未找到相关文章。可能没有匹配的内容或相似度不足。请提供更具体的查询词或重新表述问题。"

    OPENAPI_TAGS = [
        {
            "name": "AI历史模块",
            "description": "AI历史相关API，包括创建AI历史记录、获取所有AI历史记录、删除用户所有AI历史记录等",
        },
        {
            "name": "用户个人数据分析模块",
            "description": "用户个人数据分析相关API，包括获取新增粉丝数统计、获取文章浏览分布、获取关注作者统计、获取本月评论/点赞/收藏趋势等",
        },
        {
            "name": "文章分析模块",
            "description": "文章分析相关API，包括获取前10篇文章、生成词云图、获取文章统计信息等",
        },
        {
            "name": "API日志分析模块",
            "description": "API日志分析相关API，包括获取所有接口的平均响应速度、获取接口调用次数等",
        },
        {
            "name": "测试模块",
            "description": "服务测试相关API，包括测试FastAPI服务、测试Spring服务、测试GoZero服务、测试NestJS服务等",
        },
        {
            "name": "AI聊天模块",
            "description": "AI聊天相关API，包括普通聊天和流式聊天",
        },
        {
            "name": "生成模块",
            "description": "生成相关API，包括生成tags、为文章创建AI评论、为文章创建基于权威参考文本的AI评论等",
        },
        {
            "name": "知识图谱模块",
            "description": "知识图谱相关API，包括图谱搜索、图谱增强等功能",
        },
        {
            "name": "向量搜索模块",
            "description": "向量搜索相关API，包括根据 ES 候选文章进行语义分、语义原因和匹配片段增强",
        },
    ]

    OPENAPI_VERSION: str = "3.0.0"

    PERMISSION_CHECK_FAILED_MESSAGE: str = "权限检查失败"

    RABBITMQ_CONFIG_NOT_FOUND_MESSAGE: str = "RabbitMQ 配置不存在，跳过连接"

    RABBITMQ_CREATE_QUEUES_FAILURE_MESSAGE: str = "无法创建队列：RabbitMQ未连接"

    RABBITMQ_NOT_CONNECTED_MESSAGE: str = "RabbitMQ 未连接，无法发送消息"

    RAG_TOOL_NAME: str = "search_articles"

    REDIS_CLIENT_INITIALIZED_MESSAGE_PREFIX: str = "[Redis] 客户端已初始化: "

    REDIS_CONNECTION_FAILED_MESSAGE: str = "Redis 连接失败，无法获取上次同步时间戳"

    REDIS_CONNECTION_FAILED_MESSAGE_PREFIX: str = "[Redis] 连接失败: "

    REDIS_CONNECTION_SAVE_FAILED_MESSAGE: str = "Redis 连接失败，无法保存同步时间戳"

    REDIS_COROUTINE_SYNC_EXECUTION_ERROR: str = (
        "Redis 协程不能在运行中的事件循环里直接同步执行"
    )

    REDIS_DATABASE_CLEARED_MESSAGE: str = "Redis数据库已清空"

    REDIS_DELETE_FAILED_MESSAGE_PREFIX: str = "[Redis] DELETE 失败 keys="

    REDIS_EXISTS_FAILED_MESSAGE_PREFIX: str = "[Redis] EXISTS 失败 key="

    REDIS_EXPIRE_FAILED_MESSAGE_PREFIX: str = "[Redis] EXPIRE 失败 key="

    REDIS_FLUSHDB_FAILED_MESSAGE_PREFIX: str = "[Redis] FLUSHDB 失败: "

    REDIS_GET_FAILED_MESSAGE_PREFIX: str = "[Redis] GET 失败 key="

    REDIS_KEYS_FAILED_MESSAGE_PREFIX: str = "[Redis] KEYS 失败 pattern="

    REDIS_LOCK_ACQUIRE_ERROR_PREFIX: str = "[Redis] 获取分布式锁失败 key="

    REDIS_LOCK_ACQUIRE_FAIL_MESSAGE: str = (
        "[分布式锁] 获取锁失败，跳过本次执行，key: %s"
    )

    REDIS_LOCK_ACQUIRE_SUCCESS_MESSAGE: str = "[分布式锁] 获取锁成功，key: %s"

    REDIS_LOCK_RELEASE_ERROR_PREFIX: str = "[Redis] 释放分布式锁失败 key="

    REDIS_LOCK_RELEASE_FAIL_MESSAGE: str = "[分布式锁] 释放锁失败，key: %s"

    REDIS_LOCK_RELEASE_SUCCESS_MESSAGE: str = "[分布式锁] 释放锁成功，key: %s"

    REDIS_SET_FAILED_MESSAGE_PREFIX: str = "[Redis] SET 失败 key="

    REDIS_TTL_FAILED_MESSAGE_PREFIX: str = "[Redis] TTL 失败 key="

    REFERENCE_CHAT_MESSAGE: str = (
        "你是一个专业的文章评价助手。请根据提供的权威参考文本进行客观、专业的评价。"
    )

    REFERENCE_TEXT_EXTRACTION_ERROR: str = "无法提取参考文本"

    REQUEST_PROCESSING: str = "请求正在处理中"

    REQUEST_TIMEOUT_ERROR: str = "请求超时，请稍后重试。"

    REQUIRE_INTERNAL_TOKEN_ASYNC_ERROR: str = (
        "requireInternalToken 装饰器只支持异步函数"
    )

    ROLE_ADMIN: str = "admin"

    ROLE_USER: str = "user"

    SAFE_SQL_QUERY_REQUEST_PATTERNS: List[str] = [
        r"^(查询|查看|统计|列出|展示|获取|分析).*(最近|最新|已)?(更新|新增)的",
        r"^(查询|查看|统计|列出|展示|获取|分析).*(列表|数量|总数|排行|明细)",
    ]

    SCHEDULER_ANALYZE_CACHE_UPDATE_MESSAGE: str = (
        "  - 分析接口缓存更新任务：每 10 分钟执行一次（启动时立即执行）"
    )

    SCHEDULER_NEO4J_SYNC_MESSAGE: str = (
        "  - Neo4j 知识图谱同步任务：每 24 小时执行一次（启动时立即执行）"
    )

    SCHEDULER_STARTED_MESSAGE: str = "定时任务调度器已启动："

    SCHEDULER_VECTOR_SYNC_MESSAGE: str = "  - 向量同步任务：每 24 小时执行一次"

    SKIP_VERSION_CHECK: str = "[缓存] 获取当前版本号失败，跳过版本检测"

    SQL_DANGEROUS_KEYWORDS: List[str] = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "REPLACE",
        "MERGE",
        "CALL",
        "GRANT",
        "REVOKE",
        "COMMIT",
        "ROLLBACK",
        "SET",
        "USE",
        "RENAME",
        "LOCK",
        "UNLOCK",
        "HANDLER",
        "LOAD",
        "ANALYZE",
        "OPTIMIZE",
        "REPAIR",
        "KILL",
    ]

    SQL_DANGEROUS_PATTERNS: List[str] = [
        "INTO OUTFILE",
        "INTO DUMPFILE",
        "FOR UPDATE",
        "LOCK IN SHARE MODE",
    ]

    SQL_NATURAL_LANGUAGE_WRITE_BLOCK_MESSAGE: str = "安全限制：当前请求带有新增、修改、删除等数据库写操作意图。SQL 工具仅支持只读查询，请改为查询类问题。"

    SQL_QUERY_INPUT_DESC: str = "完整的只读 SQL 查询语句"

    SQL_QUERY_MULTIPLE_STATEMENTS_ERROR: str = (
        "安全限制：SQL 工具只允许执行单条只读查询，禁止多语句执行。"
    )

    SQL_QUERY_NO_RES: str = "查询成功，但没有返回结果"

    SQL_QUERY_PREFIX: str = "SELECT"

    SQL_QUERY_TOOL_NAME: str = "execute_sql_query"

    SQL_QUERY_WRITE_OPERATION_ERROR: str = (
        "安全限制：检测到 SQL 包含写操作或锁表行为，只允许执行只读查询。"
    )

    SQL_READONLY_ALLOWED_PREFIXES: List[str] = [
        "SELECT",
        "WITH",
        "SHOW",
        "DESC",
        "DESCRIBE",
        "EXPLAIN",
    ]

    SQL_TABLE_INPUT_DESC: str = "表名，留空则返回所有表"

    SQL_TABLE_TOOL_NAME: str = "get_table_schema"

    SQL_TOOL_INITIALIZATION_SUCCESS: str = "SQL工具初始化成功"

    SQL_TOOL_LIMIT: str = "安全限制：只允许执行SELECT查询语句"

    START_INITIALIZING_ARTICLE_HASH_CACHE_MESSAGE: str = (
        "开始初始化文章内容 hash 缓存..."
    )

    START_SYNC_TO_POSTGRES_MESSAGE: str = "开始同步文章内容到PostgreSQL向量库..."

    STATISTICS_CACHE_FETCH_FAILED: str = (
        "get_article_statistics_service: [缓存未命中] 开始查询数据源"
    )

    STREAMING_CHAT_THINKING_SYSTEM_MESSAGE: str = (
        "你是一个中文AI思考型助手，用于提供文章和博客推荐、日志分析以及系统数据查询的思考内容。"
        "其中 MongoDB 工具仅用于日志相关查询，例如 API 请求日志、错误日志和操作日志；"
        "系统相关数据、统计数据和业务数据必须优先使用 SQL 工具查询。"
        "当查询的数据量可能较大时，必须主动加上时间范围、用户范围、状态条件或 limit 等限制，避免一次性返回过多数据。"
        "回答文本应该展示调用工具和分析的思考过程。"
    )

    SUMMARIZE_CHAT_MESSAGE: str = (
        "你是一个专业的内容总结助手。请精准提取核心信息，用凝练的语言进行总结。"
    )

    SWAGGER_DESCRIPTION: str = "这是项目的FastAPI部分的Swagger文档"

    SWAGGER_TITLE: str = "FastAPI部分的Swagger文档"

    SWAGGER_VERSION: str = "1.0.0"

    SYNC_TIME_SET_MESSAGE: str = "已设置同步时间戳，下次同步将使用增量模式"

    TEXT_SPLITTER_INITIALIZATION_SUCCESS: str = "文本切分器初始化成功"

    TOP10_CACHE_MISS: str = "get_top10_articles_service: [缓存未命中] 开始查询数据源"

    TOP10_CLICKHOUSE_GET: str = "从ClickHouse获取Top10文章"

    TOP10_CLICKHOUSE_QUERY: str = "从ClickHouse查询Top10文章数据"

    TOP10_DB_SOURCE: str = "get_top10_articles_service: 使用 DB 数据源"

    UNKNOWN_ARTICLE: str = "未知文章"

    USER_NOT_EXISTS_ERROR: str = "用户不存在"

    USER_NOT_LOGGED_IN_MESSAGE: str = "用户未登录，请先登录"

    USER_NO_ADMIN_PERMISSION_MESSAGE: str = "权限不足，仅管理员可访问"

    USER_RELATED_TABLE: List[str] = [
        "likes",
        "collects",
        "comments",
        "ai_history",
        "chat_messages",
    ]

    VECTOR_SEARCH_REASON_HIGH: str = "语义内容与搜索词高度相关"

    VECTOR_SEARCH_REASON_LOW: str = "语义内容与搜索词存在相关性"

    VECTOR_SEARCH_REASON_MEDIUM: str = "语义内容与搜索词较相关"

    VECTOR_STORE_INITIALIZATION_SUCCESS: str = "PostgreSQL向量存储初始化成功"

    VERSION_CHANGED_CLEAR_CACHE: str = "[缓存] 版本变化，清除所有缓存"

    WORDCLOUD_CACHE_DELETED: str = "词云图缓存已删除"

    WORDCLOUD_CACHE_FETCH_FAILED: str = (
        "get_wordcloud_service: [缓存未命中] 开始生成词云图"
    )

    WORDCLOUD_FILENAME: str = "search_keywords_wordcloud.png"

    WORDCLOUD_GENERATION_SUCCESS: str = (
        "词云图生成成功，保存为 search_keywords_wordcloud.png"
    )