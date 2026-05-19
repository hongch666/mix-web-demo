from typing import Dict, List


class Constants:
    """应用常量类"""

    # 内部令牌相关常量
    INTERNAL_TOKEN_SECRET_NOT_NULL: str = "内部令牌密钥未配置"
    """内部令牌密钥未配置错误"""

    INTERNAL_TOKEN_MISSING: str = "请求头中缺少内部令牌"
    """内部令牌缺失错误"""

    INTERNAL_TOKEN_INVALID: str = "内部令牌无效"
    """内部令牌无效错误"""

    INTERNAL_TOKEN_EXPIRED: str = "内部令牌已过期"
    """内部令牌已过期错误"""

    SERVICE_NAME_MISMATCH: str = "服务名称不匹配"
    """服务名称不匹配错误"""

    TEST_MESSAGE: str = "Hello, I am FastAPI!"
    """FastAPI 测试消息"""

    AI_COMMENT_TASK_SUBMITTED: str = "AI生成评论任务已提交"
    """AI生成评论任务提交消息"""

    AI_COMMENT_WITH_REFERENCE_TASK_SUBMITTED: str = (
        "基于权威参考文本的AI生成评论任务已提交"
    )
    """基于权威参考文本的AI生成评论任务提交消息"""

    REQUEST_PROCESSING: str = "请求正在处理中"
    """请求处理中消息"""

    TOP10_CACHE_MISS: str = "get_top10_articles_service: [缓存未命中] 开始查询数据源"
    """TOP10文章缓存未命中消息"""

    TOP10_CLICKHOUSE_QUERY: str = "从ClickHouse查询Top10文章数据"
    """从ClickHouse查询Top10文章数据消息"""

    TOP10_CLICKHOUSE_GET: str = "从ClickHouse获取Top10文章"
    """从ClickHouse获取Top10文章消息"""

    TOP10_DB_SOURCE: str = "get_top10_articles_service: 使用 DB 数据源"
    """TOP10文章使用DB数据源消息"""

    KEYWORDS_EMPTY: str = "关键词字典为空，无法生成词云图"
    """关键词字典为空消息"""

    WORDCLOUD_FILENAME: str = "search_keywords_wordcloud.png"
    """词云图文件名"""

    WORDCLOUD_GENERATION_SUCCESS: str = (
        "词云图生成成功，保存为 search_keywords_wordcloud.png"
    )
    """词云图生成成功消息"""

    WORDCLOUD_CACHE_FETCH_FAILED: str = (
        "get_wordcloud_service: [缓存未命中] 开始生成词云图"
    )
    """词云图缓存获取失败消息"""

    EXPORT_ARTICLES_EXCEL_TIP: str = "文章表（本表导出自系统，包含所有文章数据）"
    """文章表导出Excel提示信息"""

    EXPORT_ARTICLES_EXCEL_FILENAME: str = "articles.xlsx"
    """文章表导出Excel文件名"""

    STATISTICS_CACHE_FETCH_FAILED: str = (
        "get_article_statistics_service: [缓存未命中] 开始查询数据源"
    )
    """文章统计信息缓存未命中消息"""

    CATEGORY_STATISTICS_CACHE_FETCH_FAILED: str = (
        "get_category_article_count_service: [缓存未命中] 开始查询数据源"
    )
    """分类文章统计缓存未命中消息"""

    CATEGORY_STATISTICS_CLICKHOUSE_QUERY: str = "从ClickHouse查询分类文章统计数据"
    """从ClickHouse查询分类文章统计数据消息"""

    CATEGORY_STATISTICS_CLICKHOUSE_GET: str = "从ClickHouse获取分类文章统计"
    """从ClickHouse获取分类文章统计消息"""

    CATEGORY_STATISTICS_DB_SOURCE: str = (
        "get_category_article_count_service: 使用 DB 数据源"
    )
    """分类文章统计使用DB数据源消息"""

    MONTHLY_STATISTICS_CACHE_FETCH_FAILED: str = (
        "get_monthly_publish_count_service: [缓存未命中] 开始查询数据源"
    )
    """月度文章统计缓存未命中消息"""

    MONTHLY_STATISTICS_CLICKHOUSE_QUERY: str = "从ClickHouse查询月度发布统计数据"
    """从ClickHouse查询月度发布统计数据消息"""

    MONTHLY_STATISTICS_CLICKHOUSE_GET: str = "从ClickHouse获取月度发布统计"
    """从ClickHouse获取月度发布统计消息"""

    MONTHLY_STATISTICS_DB_SOURCE: str = (
        "get_monthly_publish_count_service: 使用 DB 数据源"
    )
    """月度文章统计使用DB数据源消息"""

    DEEPSEEK_AGENT_INITIALIZATION_SUCCESS: str = "DeepSeek Agent服务初始化完成"
    """DeepSeek Agent初始化成功"""

    DEEPSEEK_CONFIGURATION_INCOMPLETE_ERROR: str = "DeepSeek配置不完整，客户端未初始化"
    """DeepSeek配置不完整错误消息"""

    INITIALIZATION_ERROR: str = "聊天服务未配置或初始化失败"
    """初始化错误消息"""

    GENERIC_CHAT_MESSAGE: str = (
        "你是一个中文AI助手，用于提供文章和博客推荐及分析系统数据。"
    )
    """普通系统消息"""

    REFERENCE_CHAT_MESSAGE: str = (
        "你是一个专业的文章评价助手。请根据提供的权威参考文本进行客观、专业的评价。"
    )
    """基于参考文本的聊天系统消息"""

    SUMMARIZE_CHAT_MESSAGE: str = (
        "你是一个专业的内容总结助手。请精准提取核心信息，用凝练的语言进行总结。"
    )
    """总结功能的系统消息"""

    CHAT_SYSTEM_MESSAGE: str = (
        "你是一个中文AI助手，用于提供文章和博客推荐及分析系统数据。"
    )
    """聊天功能的系统消息"""

    STREAMING_CHAT_THINKING_SYSTEM_MESSAGE: str = (
        "你是一个中文AI思考型助手，用于提供文章和博客推荐、日志分析以及系统数据查询的思考内容。"
        "其中 MongoDB 工具仅用于日志相关查询，例如 API 请求日志、错误日志和操作日志；"
        "系统相关数据、统计数据和业务数据必须优先使用 SQL 工具查询。"
        "当查询的数据量可能较大时，必须主动加上时间范围、用户范围、状态条件或 limit 等限制，避免一次性返回过多数据。"
        "回答文本应该展示调用工具和分析的思考过程。"
    )
    """流式聊天思考过程系统消息"""

    AGENT_PROCESSING_MESSAGE: str = (
        "使用Agent处理，可同时调用SQL、RAG和Neo4j知识图谱工具"
    )
    """Agent处理消息"""

    AGENT_PARSING_ERROR_HINT: str = (
        "上一轮回复格式不正确，请严格按以下格式输出，并且不要输出多余内容：\n"
        "Thought: 先思考\n"
        "Action: 从工具列表中选择一个工具名\n"
        "Action Input: 工具输入\n"
        "如果已经有最终答案，再输出：\n"
        "Final Answer: 最终回答"
    )
    """Agent解析失败提示"""

    AGENT_START_PROCESSING_MESSAGE: str = "Agent开始处理..."
    """Agent开始处理消息"""

    MESSAGE_RETRIEVAL_ERROR: str = "无法获取结果"
    """消息获取错误"""

    NO_PERMISSION_ERROR: str = "您没有权限访问此功能，请联系管理员开通相关权限。"
    """没有权限访问相关数据的提示信息"""

    AGENT_START_STREAMING_MESSAGE: str = "Agent思考完成,开始流式输出优化后的答案"
    """开始流式输出消息"""

    GEMINI_AGENT_INITIALIZATION_SUCCESS: str = "Gemini Agent服务初始化完成"
    """Gemini Agent初始化成功"""

    GEMINI_CONFIGURATION_INCOMPLETE_ERROR: str = "Gemini配置不完整，客户端未初始化"
    """Gemini配置不完整错误消息"""

    GEMINI_INVALID_API_KEY_ERROR: str = "API密钥无效。请检查Gemini API密钥配置。"
    """Gemini密钥无效消息"""

    GEMINI_QUOTA_EXCEEDED_ERROR: str = "Gemini API 配额已用完。请稍后重试。"
    """Gemini配额用尽消息"""

    GEMINI_RATE_LIMIT_EXCEEDED_ERROR: str = "Gemini API调用频率超限。请稍后重试。"
    """Gemini调用频率超限消息"""

    REQUEST_TIMEOUT_ERROR: str = "请求超时，请稍后重试。"
    """请求超时错误消息"""

    GPT_AGENT_INITIALIZATION_SUCCESS: str = "GPT Agent服务初始化完成"
    """GPT Agent初始化成功"""

    GPT_CONFIGURATION_INCOMPLETE_ERROR: str = "GPT配置不完整，客户端未初始化"
    """GPT配置不完整错误消息"""

    GPT_INVALID_API_KEY_ERROR: str = "API密钥无效。请检查GPT API密钥配置。"
    """GPT密钥无效消息"""

    GPT_QUOTA_EXCEEDED_ERROR: str = "GPT API 配额已用完。请稍后重试。"
    """GPT配额用尽消息"""

    GPT_RATE_LIMIT_EXCEEDED_ERROR: str = "GPT API调用频率超限。请稍后重试。"
    """GPT调用频率超限消息"""

    DEEPSEEK_CALL_FAILED_ERROR: str = "DeepSeek调用失败"
    """DeepSeek调用失败消息"""

    GEMINI_CALL_FAILED_ERROR: str = "Gemini调用失败"
    """Gemini调用失败消息"""

    GPT_CALL_FAILED_ERROR: str = "GPT调用失败"
    """GPT调用失败消息"""

    CATEGORY_NO_AUTHORITATIVE_REFERENCE_TEXT_ERROR: str = (
        "该分类暂无权威参考文本，请根据您的专业知识进行评价。"
    )
    """分类无权威参考文本错误消息"""

    REFERENCE_TEXT_EXTRACTION_ERROR: str = "无法提取参考文本"
    """无法提取参考文本错误消息"""

    CONCURRENT_SUMMARY_MESSAGE: str = "开始并发调用三个大模型进行总结"
    """并发总结消息"""

    CONCURRENT_CHAT_MESSAGE_SUCCESS: str = "权威文章生成完成，所有大模型总结已完成"
    """并发聊天完成消息"""

    SWAGGER_TITLE: str = "FastAPI部分的Swagger文档"
    """Swagger 文档标题"""

    SWAGGER_DESCRIPTION: str = "这是项目的FastAPI部分的Swagger文档"
    """Swagger 文档描述"""

    SWAGGER_VERSION: str = "1.0.0"
    """Swagger 文档版本"""

    STARTUP_MESSAGE: str = "FastAPI应用已启动"
    """启动消息"""

    INIT_IP: str = "127.0.0.1"
    """初始IP地址"""

    NACOS_REGISTER_DEV_MODE_MESSAGE: str = (
        "SERVER_MODE=dev，Nacos 注册统一使用 127.0.0.1"
    )
    """dev 模式下 Nacos 注册日志"""

    INTENT_ROUTER_NO_PERMISSION_ERROR: str = "权限拒绝：此功能需要登录后才能使用。请先登录您的账户。您可以继续使用文章搜索和闲聊功能。"
    """意图识别权限拒绝信息"""

    COLLECTION_NAME_VALIDATION_ERROR: str = "错误: 必须提供 collection_name 参数"
    """collection_name参数验证错误消息"""

    TEXT_SPLITTER_INITIALIZATION_SUCCESS: str = "文本切分器初始化成功"
    """文本切分器初始化"""

    VECTOR_STORE_INITIALIZATION_SUCCESS: str = "PostgreSQL向量存储初始化成功"
    """向量存储初始化成功消息"""

    NO_RELEVANT_ARTICLES_FOUND_MESSAGE: str = "未找到相关文章。可能没有匹配的内容或相似度不足。请提供更具体的查询词或重新表述问题。"
    """未找到相关文章提示消息"""

    SQL_TOOL_INITIALIZATION_SUCCESS: str = "SQL工具初始化成功"
    """SQL工具初始化成功消息"""

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
    """默认关键字"""

    L1_CACHE_TTL_EXPIRED: str = "[L1缓存] TTL过期"
    """L1缓存TTL过期消息"""

    L2_CACHE_UNAVAILABLE: str = "[L2缓存] Redis 不可用"
    """L2缓存不可用消息"""

    L2_CACHE_HIT: str = "[L2缓存] 命中 Redis"
    """L2缓存命中消息"""

    L2_CACHE_MISS: str = "[L2缓存] Redis 未命中"
    """L2缓存未命中消息"""

    SKIP_VERSION_CHECK: str = "[缓存] 获取当前版本号失败，跳过版本检测"
    """跳过版本号检查常量"""

    VERSION_CHANGED_CLEAR_CACHE: str = "[缓存] 版本变化，清除所有缓存"
    """版本变化清除缓存消息"""

    CLICKHOUSE_CONNECTION_POOL_FULL_MESSAGE: str = (
        "[ClickHouse连接池] 连接池已满，连接已关闭"
    )
    """ClickHouse连接池满消息"""

    CLICKHOUSE_CONNECTION_POOL_CLOSED_MESSAGE: str = "[ClickHouse连接池] 所有连接已关闭"
    """ClickHouse所有连接已关闭消息"""

    CLICKHOUSE_CACHE_MISS_QUERY_MESSAGE: str = "ClickHouse缓存未命中，将查询数据源"
    """ClickHouse缓存未命中消息"""

    DB_CACHE_MISS_QUERY_DB_MESSAGE: str = "[缓存] L1/L2 都未命中，需要查询 DB"
    """缓存未命中查询DB消息"""

    L1_CACHE_UPDATED: str = "[L1缓存] 已更新"
    """L1缓存更新消息"""

    L1_CACHE_CLEARED: str = "[L1缓存] 已清除"
    """L1缓存清除消息"""

    L2_CACHE_CLEARED: str = "[L2缓存] Redis 已清除"
    """L2缓存清除消息"""

    WORDCLOUD_CACHE_DELETED: str = "词云图缓存已删除"
    """词云图缓存删除消息"""

    RABBITMQ_NOT_AVAILABLE: str = "日志装饰器捕获到异常，请检查日志详情"
    """日志装饰器异常捕获消息"""

    API_RABBITMQ_LOGGING_SUCCESS: str = "API 日志已发送到队列"
    """API日志消息发送成功消息"""

    API_RABBITMQ_LOGGING_FAILURE: str = "API 日志发送到队列失败"
    """API日志消息发送失败消息"""

    EXCEPTION_HANDLER_MESSAGE: str = "FastAPI服务器错误"
    """异常处理统一消息"""

    # 错误标识常量 - 用于区分同一状态码下的不同错误场景

    # 400 Bad Request
    ERROR_PARAM_PARSE_FAILED: str = "PARAM_PARSE_FAILED"
    """参数解析失败"""

    ERROR_COLLECTION_NAME_REQUIRED: str = "COLLECTION_NAME_REQUIRED"
    """必须提供 collection_name 参数"""

    # 401 Unauthorized
    ERROR_USER_NOT_LOGIN: str = "USER_NOT_LOGIN"
    """用户未登录"""

    ERROR_INTERNAL_TOKEN_MISSING: str = "INTERNAL_TOKEN_MISSING"
    """缺少必需的内部服务令牌请求头"""

    ERROR_INTERNAL_TOKEN_INVALID: str = "INTERNAL_TOKEN_INVALID"
    """内部服务令牌无效"""

    ERROR_INTERNAL_TOKEN_EXPIRED: str = "INTERNAL_TOKEN_EXPIRED"
    """内部服务令牌已过期"""

    # 403 Forbidden
    ERROR_PERMISSION_CHECK_FAILED: str = "PERMISSION_CHECK_FAILED"
    """权限检查失败"""

    ERROR_NO_ADMIN_PERMISSION: str = "NO_ADMIN_PERMISSION"
    """当前用户没有管理员权限"""

    ERROR_USER_NO_ADMIN_PERMISSION: str = "USER_NO_ADMIN_PERMISSION"
    """权限不足，仅管理员可访问"""

    ERROR_INTENT_ROUTER_NO_PERMISSION: str = "INTENT_ROUTER_NO_PERMISSION"
    """权限拒绝：此功能需要登录后才能使用"""

    ERROR_INTERNAL_TOKEN_SERVICE_MISMATCH: str = "INTERNAL_TOKEN_SERVICE_MISMATCH"
    """服务名称不匹配"""

    # 404 Not Found
    ERROR_USER_NOT_FOUND: str = "USER_NOT_FOUND"
    """用户不存在"""

    ERROR_ARTICLE_NOT_FOUND: str = "ARTICLE_NOT_FOUND"
    """文章不存在"""

    ERROR_NO_RELEVANT_ARTICLES: str = "NO_RELEVANT_ARTICLES"
    """未找到相关文章"""

    ERROR_AI_CHAT_NO_INSTANCE: str = "AI_CHAT_NO_INSTANCE"
    """找不到可用的服务实例"""

    # 429 Too Many Requests
    ERROR_GEMINI_QUOTA_EXCEEDED: str = "GEMINI_QUOTA_EXCEEDED"
    """Gemini API 配额已用完"""

    ERROR_GEMINI_RATE_LIMIT_EXCEEDED: str = "GEMINI_RATE_LIMIT_EXCEEDED"
    """Gemini API调用频率超限"""

    ERROR_GPT_RATE_LIMIT_EXCEEDED: str = "GPT_RATE_LIMIT_EXCEEDED"
    """GPT API调用频率超限"""

    # 500 Internal Server Error
    ERROR_FASTAPI_SERVER_ERROR: str = "FASTAPI_SERVER_ERROR"
    """FastAPI服务器错误"""

    ERROR_DEEPSEEK_CALL_FAILED: str = "DEEPSEEK_CALL_FAILED"
    """DeepSeek调用失败"""

    ERROR_GEMINI_CALL_FAILED: str = "GEMINI_CALL_FAILED"
    """Gemini调用失败"""

    # 502 Bad Gateway
    ERROR_GPT_CALL_FAILED: str = "GPT_CALL_FAILED"
    """GPT调用失败"""

    ERROR_SERVICE_CALL_FAILED: str = "SERVICE_CALL_FAILED"
    """服务调用失败"""

    UNKNOWN_ERROR: str = "未知错误"
    """未知错误"""

    # 503 Service Unavailable
    ERROR_RABBITMQ_CLIENT_NOT_INITIALIZED: str = "RABBITMQ_CLIENT_NOT_INITIALIZED"
    """RabbitMQ客户端未初始化"""

    ERROR_RABBITMQ_NOT_CONNECTED: str = "RABBITMQ_NOT_CONNECTED"
    """RabbitMQ未连接"""

    ERROR_RABBITMQ_CONFIG_NOT_FOUND: str = "RABBITMQ_CONFIG_NOT_FOUND"
    """RabbitMQ配置不存在"""

    ERROR_OSS_CLIENT_NOT_INITIALIZED: str = "OSS_CLIENT_NOT_INITIALIZED"
    """OSS客户端尚未初始化"""

    ERROR_DEEPSEEK_NOT_CONFIGURED: str = "DEEPSEEK_NOT_CONFIGURED"
    """DeepSeek配置不完整，客户端未初始化"""

    ERROR_GEMINI_NOT_CONFIGURED: str = "GEMINI_NOT_CONFIGURED"
    """Gemini配置不完整，客户端未初始化"""

    ERROR_GPT_NOT_CONFIGURED: str = "GPT_NOT_CONFIGURED"
    """GPT配置不完整，客户端未初始化"""

    ERROR_INITIALIZATION_ERROR: str = "INITIALIZATION_ERROR"
    """聊天服务未配置或初始化失败"""

    ERROR_SERVICE_DISCOVERY_FAILED: str = "SERVICE_DISCOVERY_FAILED"
    """服务发现失败"""

    ERROR_NO_AVAILABLE_SERVICE_INSTANCE: str = "NO_AVAILABLE_SERVICE_INSTANCE"
    """无可用服务实例"""

    # 504 Gateway Timeout
    ERROR_REQUEST_TIMEOUT: str = "REQUEST_TIMEOUT"
    """请求超时"""

    ERROR_OSS_PUT_TIMEOUT: str = "OSS_PUT_TIMEOUT"
    """OSS put 操作超时"""

    # 500 内部令牌
    ERROR_INTERNAL_TOKEN_SECRET_NOT_NULL: str = "INTERNAL_TOKEN_SECRET_NOT_NULL"
    """内部服务令牌密钥未配置"""

    AI_CHAT_TABLE_CREATION_MESSAGE: str = "ai_history 表创建完成"
    """表创建完成消息"""

    AI_CHAT_TABLE_EXISTS_MESSAGE: str = "ai_history 表已存在"
    """表已存在消息"""

    AI_CHAT_TABLE_UNSUPPORTED_MESSAGE: str = "仅支持创建 ai_history 表"
    """仅支持创建 ai_history 表消息"""

    AI_CHAT_NO_INSTANCE_MESSAGE: str = "找不到可用的服务实例"
    """找不到实例消息"""

    RABBITMQ_CLIENT_NOT_INITIALIZED_MESSAGE: str = (
        "RabbitMQ 客户端未初始化，无法发送消息到队列"
    )
    """RabbitMQ客户端未初始化消息"""

    RABBITMQ_CONFIG_NOT_FOUND_MESSAGE: str = "RabbitMQ 配置不存在，跳过连接"
    """RabbitMQ配置不存在消息"""

    RABBITMQ_NOT_CONNECTED_MESSAGE: str = "RabbitMQ 未连接，无法发送消息"
    """RabbitMQ未连接消息"""

    RABBITMQ_CREATE_QUEUES_FAILURE_MESSAGE: str = "无法创建队列：RabbitMQ未连接"
    """无法创建队列消息"""

    RABBITMQ_CONNECTION_CLOSED_MESSAGE: str = "RabbitMQ 连接已关闭"
    """RabbitMQ连接关闭消息"""

    REDIS_DATABASE_CLEARED_MESSAGE: str = "Redis数据库已清空"
    """Redis数据库已清空消息"""

    REDIS_CLIENT_INITIALIZED_MESSAGE_PREFIX: str = "[Redis] 客户端已初始化: "
    """Redis 客户端初始化前缀消息"""

    REDIS_CONNECTION_FAILED_MESSAGE_PREFIX: str = "[Redis] 连接失败: "
    """Redis 连接失败前缀消息"""

    REDIS_GET_FAILED_MESSAGE_PREFIX: str = "[Redis] GET 失败 key="
    """Redis GET 失败前缀消息"""

    REDIS_SET_FAILED_MESSAGE_PREFIX: str = "[Redis] SET 失败 key="
    """Redis SET 失败前缀消息"""

    REDIS_DELETE_FAILED_MESSAGE_PREFIX: str = "[Redis] DELETE 失败 keys="
    """Redis DELETE 失败前缀消息"""

    REDIS_EXISTS_FAILED_MESSAGE_PREFIX: str = "[Redis] EXISTS 失败 key="
    """Redis EXISTS 失败前缀消息"""

    REDIS_EXPIRE_FAILED_MESSAGE_PREFIX: str = "[Redis] EXPIRE 失败 key="
    """Redis EXPIRE 失败前缀消息"""

    REDIS_TTL_FAILED_MESSAGE_PREFIX: str = "[Redis] TTL 失败 key="
    """Redis TTL 失败前缀消息"""

    REDIS_KEYS_FAILED_MESSAGE_PREFIX: str = "[Redis] KEYS 失败 pattern="
    """Redis KEYS 失败前缀消息"""

    REDIS_FLUSHDB_FAILED_MESSAGE_PREFIX: str = "[Redis] FLUSHDB 失败: "
    """Redis FLUSHDB 失败前缀消息"""

    ASYNC_SYNC_CALL_IN_EVENT_LOOP_ERROR: str = (
        "同步方法不能在运行中的事件循环里直接调用"
    )
    """同步方法在事件循环中调用错误"""

    REDIS_COROUTINE_SYNC_EXECUTION_ERROR: str = (
        "Redis 协程不能在运行中的事件循环里直接同步执行"
    )
    """Redis 协程同步执行错误"""

    UPDATE_ANALYZE_CACHES_ANALYZE_SERVICE_NONE_MESSAGE: str = (
        "update_analyze_caches: analyze_service 为 None，跳过缓存更新"
    )
    """更新分析缓存时 analyze_service 为 None 消息"""

    UPDATE_ANALYZE_CACHES_START_MESSAGE: str = "开始更新分析接口缓存"
    """开始更新分析接口缓存消息"""

    UPDATE_ANALYZE_CACHES_TOP10_START_MESSAGE: str = "更新前10篇文章缓存..."
    """更新前10篇文章缓存开始消息"""

    UPDATE_ANALYZE_CACHES_TOP10_SUCCESS_MESSAGE: str = "前10篇文章缓存更新成功"
    """前10篇文章缓存更新成功消息"""

    UPDATE_ANALYZE_CACHES_WORDCLOUD_START_MESSAGE: str = "更新词云图缓存..."
    """更新词云图缓存开始消息"""

    UPDATE_ANALYZE_CACHES_WORDCLOUD_SUCCESS_MESSAGE: str = "词云图缓存更新成功"
    """词云图缓存更新成功消息"""

    UPDATE_ANALYZE_CACHES_STATISTICS_START_MESSAGE: str = "更新文章统计信息缓存..."
    """更新文章统计信息缓存开始消息"""

    UPDATE_ANALYZE_CACHES_STATISTICS_SUCCESS_MESSAGE: str = "文章统计信息缓存更新成功"
    """文章统计信息缓存更新成功消息"""

    UPDATE_ANALYZE_CACHES_CATEGORY_STATISTICS_START_MESSAGE: str = (
        "更新按分类统计文章数量缓存..."
    )
    """更新按分类统计文章数量缓存开始消息"""

    UPDATE_ANALYZE_CACHES_CATEGORY_STATISTICS_SUCCESS_MESSAGE: str = (
        "按分类统计文章数量缓存更新成功"
    )
    """按分类统计文章数量缓存更新成功消息"""

    UPDATE_ANALYZE_CACHES_MONTHLY_STATISTICS_START_MESSAGE: str = (
        "更新月度文章发布统计缓存..."
    )
    """更新月度文章发布统计缓存开始消息"""

    UPDATE_ANALYZE_CACHES_MONTHLY_STATISTICS_SUCCESS_MESSAGE: str = (
        "月度文章发布统计缓存更新成功"
    )
    """月度文章发布统计缓存更新成功消息"""

    UPDATE_ANALYZE_CACHES_COMPLETE_MESSAGE: str = "分析接口缓存更新完成"
    """分析接口缓存更新完成消息"""

    SCHEDULER_STARTED_MESSAGE: str = "定时任务调度器已启动："
    """调度器启动消息"""

    SCHEDULER_VECTOR_SYNC_MESSAGE: str = "  - 向量同步任务：每 24 小时执行一次"
    """调度器向量同步任务消息"""

    SCHEDULER_ANALYZE_CACHE_UPDATE_MESSAGE: str = (
        "  - 分析接口缓存更新任务：每 10 分钟执行一次（启动时立即执行）"
    )
    """调度器分析接口缓存更新任务消息"""

    SCHEDULER_NEO4J_SYNC_MESSAGE: str = (
        "  - Neo4j 知识图谱同步任务：每 24 小时执行一次（启动时立即执行）"
    )
    """调度器 Neo4j 知识图谱同步任务消息"""

    NO_ARTICLES_DATA_MESSAGE: str = "没有文章数据"
    """没有文章数据消息"""

    NO_CHANGED_ARTICLES_MESSAGE: str = "没有文章内容变更，跳过向量库同步"
    """没有文章内容变更消息"""

    NO_PUBLISHED_ARTICLES_MESSAGE: str = "没有已发布的文章需要同步"
    """没有已发布的文章需要同步消息"""

    START_INITIALIZING_ARTICLE_HASH_CACHE_MESSAGE: str = (
        "开始初始化文章内容 hash 缓存..."
    )
    """开始初始化文章内容 hash 缓存消息"""

    ARTICLE_MAPPER_METHOD_MISSING_ERROR: str = "ArticleMapper 未提供获取文章的方法"
    """ArticleMapper 未提供获取文章的方法错误消息"""

    SYNC_TIME_SET_MESSAGE: str = "已设置同步时间戳，下次同步将使用增量模式"
    """已设置同步时间戳消息"""

    REDIS_CONNECTION_FAILED_MESSAGE: str = "Redis 连接失败，无法获取上次同步时间戳"
    """无法连接到 Redis 服务器无法获取上次同步时间戳消息"""

    REDIS_CONNECTION_SAVE_FAILED_MESSAGE: str = "Redis 连接失败，无法保存同步时间戳"
    """无法连接到 Redis 服务器无法保存同步时间戳消息"""

    FIRST_TIME_SYNC_MESSAGE: str = "首次同步向量库，将同步所有已发布文章"
    """首次向量同步任务消息"""

    START_SYNC_TO_POSTGRES_MESSAGE: str = "开始同步文章内容到PostgreSQL向量库..."
    """同步文章内容到 PostgreSQL 向量库消息"""

    USER_NOT_LOGGED_IN_MESSAGE: str = "用户未登录，请先登录"
    """用户未登录消息"""

    USER_NO_ADMIN_PERMISSION_MESSAGE: str = "权限不足，仅管理员可访问"
    """权限不足消息"""

    PERMISSION_CHECK_FAILED_MESSAGE: str = "权限检查失败"
    """权限检查失败消息"""

    USER_NOT_EXISTS_ERROR: str = "用户不存在"
    """用户不存在错误消息"""

    ARTICLE_NOT_EXISTS_ERROR: str = "文章不存在"
    """文章不存在错误消息"""

    UNKNOWN_ARTICLE: str = "未知文章"
    """未知文章消息"""

    GET_TOP_FAIL: str = "获取文章浏览分布失败"
    """获取文章浏览分布失败消息"""

    APILOG_ASYNC_ERROR: str = "apiLog 装饰器只支持异步函数"
    """apiLog 装饰器只支持异步函数消息"""

    REQUIRE_INTERNAL_TOKEN_ASYNC_ERROR: str = (
        "requireInternalToken 装饰器只支持异步函数"
    )
    """requireInternalToken 装饰器只支持异步函数消息"""

    AIO_PKA_EVENT_LOOP_ERROR: str = "检测到运行中的事件循环，跳过 RabbitMQ 同步关闭"
    """检测到运行中的事件循环错误消息"""

    NACOS_REGISTER_SUCCESS: str = "Nacos 服务注册成功"
    """Nacos 服务注册成功消息"""

    NACOS_INITIALIZATION_FAILED: str = "nacos 初始化不可用"
    """Nacos 初始化失败错误消息"""

    REDIS_LOCK_ACQUIRE_ERROR_PREFIX: str = "[Redis] 获取分布式锁失败 key="
    """获取分布式锁错误前缀消息"""

    REDIS_LOCK_RELEASE_ERROR_PREFIX: str = "[Redis] 释放分布式锁失败 key="
    """释放分布式锁错误前缀消息"""

    LOCK_TASK_VECTOR_SYNC: str = "lock:task:vector:sync"
    """向量同步任务分布式锁的 key"""

    LOCK_TASK_VECTOR_SYNC_EXPIRE: int = 86400
    """向量同步任务分布式锁的过期时间（秒），与任务执行间隔一致（24小时）"""

    LOCK_TASK_ANALYZE_CACHE: str = "lock:task:analyze:cache"
    """分析缓存更新任务分布式锁的 key"""

    LOCK_TASK_ANALYZE_CACHE_EXPIRE: int = 600
    """分析缓存更新任务分布式锁的过期时间（秒），与任务执行间隔一致（10分钟）"""

    LOCK_TASK_NEO4J_SYNC: str = "lock:task:neo4j:sync"
    """Neo4j 知识图谱同步任务分布式锁的 key"""

    LOCK_TASK_NEO4J_SYNC_EXPIRE: int = 3600
    """Neo4j 知识图谱同步任务分布式锁的过期时间（秒）"""

    NEO4J_SYNC_START_MESSAGE: str = "[知识图谱] 开始全量同步 MySQL 到 Neo4j"
    """Neo4j 知识图谱全量同步开始消息"""

    NEO4J_INCREMENTAL_SYNC_START_MESSAGE: str = "[知识图谱] 开始增量同步 MySQL 到 Neo4j"
    """Neo4j 知识图谱增量同步开始消息"""

    NEO4J_TASK_START_MESSAGE: str = "[知识图谱任务] 开始执行 MySQL 到 Neo4j 全量同步"
    """Neo4j 知识图谱定时任务开始消息"""

    NEO4J_TASK_FINISH_MESSAGE: str = "[知识图谱任务] MySQL 到 Neo4j 同步完成: %s"
    """Neo4j 知识图谱定时任务完成消息"""

    NEO4J_GRAPH_EMPTY_FULL_SYNC_MESSAGE: str = "Neo4j 当前无图谱数据，切换为全量同步"
    """Neo4j 空图谱全量同步消息"""

    NEO4J_NO_INCREMENTAL_DATA_MESSAGE: str = "没有检测到需要同步的 Neo4j 增量数据"
    """Neo4j 无增量数据消息"""

    NEO4J_CLEANUP_DELETED_DATA_START_MESSAGE: str = (
        "[知识图谱] 开始清理 Neo4j 中已删除的 MySQL 数据"
    )
    """Neo4j 删除同步清理开始消息"""

    REDIS_LOCK_ACQUIRE_SUCCESS_MESSAGE: str = "[分布式锁] 获取锁成功，key: %s"
    """获取分布式锁成功消息"""

    REDIS_LOCK_ACQUIRE_FAIL_MESSAGE: str = (
        "[分布式锁] 获取锁失败，跳过本次执行，key: %s"
    )
    """获取分布式锁失败消息"""

    REDIS_LOCK_RELEASE_SUCCESS_MESSAGE: str = "[分布式锁] 释放锁成功，key: %s"
    """释放分布式锁成功消息"""

    REDIS_LOCK_RELEASE_FAIL_MESSAGE: str = "[分布式锁] 释放锁失败，key: %s"
    """释放分布式锁失败消息"""

    CIRCUIT_BREAKER_OPEN: str = "熔断器已打开，跳过远程调用"
    """熔断器打开消息"""

    # SQL 语句

    AI_CHAT_SQL_TABLE_EXISTENCE_CHECK: str = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'ai_history'"
    """检查AI聊天表是否存在的SQL常量"""

    AI_CHAT_SQL_TABLE_CREATION_MESSAGE: str = """
        CREATE TABLE `ai_history` (
            `id` BIGINT NOT NULL AUTO_INCREMENT,
            `user_id` BIGINT,
            `ask` TEXT NOT NULL,
            `reply` TEXT NOT NULL,
            `thinking` TEXT,
            `ai_type` VARCHAR(30),
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`),
            KEY `idx_user_id` (`user_id`)
        ) COMMENT='AI聊天记录' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    """SQL创建AI聊天表常量"""

    NEO4J_SQL_SELECT_USERS: str = (
        "SELECT id, name, email, role, img, signature, create_at, update_at FROM user"
    )
    """Neo4j 同步查询用户 SQL"""

    NEO4J_SQL_SELECT_CATEGORIES: str = "SELECT id, name, update_time FROM category"
    """Neo4j 同步查询主分类 SQL"""

    NEO4J_SQL_SELECT_SUB_CATEGORIES: str = (
        "SELECT id, name, category_id, update_time FROM sub_category"
    )
    """Neo4j 同步查询子分类 SQL"""

    NEO4J_SQL_SELECT_ARTICLES: str = (
        "SELECT id, title, tags, status, views, user_id, sub_category_id, "
        "create_at, update_at, content FROM articles"
    )
    """Neo4j 同步查询文章 SQL"""

    NEO4J_SQL_SELECT_LIKES: str = "SELECT user_id, article_id, created_time FROM likes"
    """Neo4j 同步查询点赞 SQL"""

    NEO4J_SQL_SELECT_COLLECTS: str = (
        "SELECT user_id, article_id, created_time FROM collects"
    )
    """Neo4j 同步查询收藏 SQL"""

    NEO4J_SQL_SELECT_COMMENTS: str = (
        "SELECT id, user_id, article_id, create_time, update_time FROM comments"
    )
    """Neo4j 同步查询评论 SQL"""

    NEO4J_SQL_SELECT_FOCUS: str = "SELECT user_id, focus_id, created_time FROM focus"
    """Neo4j 同步查询关注关系 SQL"""

    NEO4J_SQL_INCREMENTAL_SUFFIX_FORMAT: str = "%s WHERE %s >= '%s' ORDER BY %s ASC"
    """Neo4j 同步增量 SQL 拼接格式"""

    SQL_QUERY_PREFIX: str = "SELECT"
    """SQL查询前缀"""

    SQL_READONLY_ALLOWED_PREFIXES: List[str] = [
        "SELECT",
        "WITH",
        "SHOW",
        "DESC",
        "DESCRIBE",
        "EXPLAIN",
    ]
    """只读SQL允许的起始关键字"""

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
    """SQL中禁止出现的危险关键字"""

    SQL_DANGEROUS_PATTERNS: List[str] = [
        "INTO OUTFILE",
        "INTO DUMPFILE",
        "FOR UPDATE",
        "LOCK IN SHARE MODE",
    ]
    """SQL中禁止出现的危险片段"""

    DANGEROUS_SQL_REQUEST_PATTERNS: List[str] = [
        r"\b(update|delete|insert|drop|alter|truncate|create|replace|merge)\b",
        r"(把|将).*(修改|更新|删除|新增|插入|写入|创建|清空|重置|下架|发布|设为|设置为|改成|改为)",
        r"(帮我|请|给我|直接|批量).*(修改|更新|删除|新增|插入|写入|创建|清空|重置|下架|发布|设为|设置为|改成|改为).*(数据库|数据|表|记录|文章|用户|评论|点赞|收藏|status|状态|字段)",
        r"(修改|更新|删除|新增|插入|写入|创建|清空|重置).*(数据库|数据|表|记录|文章|用户|评论|点赞|收藏|status|状态|字段)",
        r"(删除|清空|重置).*(数据|记录|表|文章|用户|评论)",
        r"(新增|插入|写入|创建).*(数据|记录|表|文章|用户|评论)",
    ]
    """自然语言中疑似引导生成写操作SQL的模式"""

    SAFE_SQL_QUERY_REQUEST_PATTERNS: List[str] = [
        r"^(查询|查看|统计|列出|展示|获取|分析).*(最近|最新|已)?(更新|新增)的",
        r"^(查询|查看|统计|列出|展示|获取|分析).*(列表|数量|总数|排行|明细)",
    ]
    """自然语言中明确的只读查询模式"""

    # Cypher 语句

    NEO4J_CREATE_CONSTRAINTS: List[str] = [
        "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
        "CREATE CONSTRAINT category_id_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT sub_category_id_unique IF NOT EXISTS FOR (s:SubCategory) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT article_id_unique IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE",
        "CREATE CONSTRAINT tag_name_unique IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE",
    ]
    """Neo4j 约束创建语句列表"""

    NEO4J_MERGE_USERS_CYPHER: str = """
        UNWIND $rows AS row
        MERGE (u:User {id: row.id})
        SET u.name = row.name,
            u.email = row.email,
            u.role = row.role,
            u.img = row.img,
            u.signature = row.signature,
            u.createdAt = row.createdAt,
            u.updatedAt = row.updatedAt
    """
    """Neo4j 合并用户节点 Cypher"""

    NEO4J_MERGE_CATEGORIES_CYPHER: str = """
        UNWIND $rows AS row
        MERGE (c:Category {id: row.id})
        SET c.name = row.name,
            c.updatedAt = row.updatedAt
    """
    """Neo4j 合并主分类节点 Cypher"""

    NEO4J_MERGE_SUB_CATEGORIES_CYPHER: str = """
        UNWIND $rows AS row
        MERGE (s:SubCategory {id: row.id})
        SET s.name = row.name,
            s.categoryId = row.categoryId,
            s.updatedAt = row.updatedAt
    """
    """Neo4j 合并子分类节点 Cypher"""

    NEO4J_MERGE_ARTICLES_CYPHER: str = """
        UNWIND $rows AS row
        MERGE (a:Article {id: row.id})
        SET a.title = row.title,
            a.tags = row.tags,
            a.status = row.status,
            a.views = row.views,
            a.createAt = row.createAt,
            a.updateAt = row.updateAt,
            a.contentHash = row.contentHash,
            a.updatedAt = row.updatedAt
    """
    """Neo4j 合并文章节点 Cypher"""

    NEO4J_MERGE_TAGS_CYPHER: str = """
        UNWIND $rows AS row
        MERGE (t:Tag {name: row.name})
    """
    """Neo4j 合并标签节点 Cypher"""

    NEO4J_MERGE_SUB_CATEGORY_TO_CATEGORY_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (s:SubCategory {id: row.subCategoryId})
        MATCH (c:Category {id: row.categoryId})
        MERGE (s)-[:BELONGS_TO_CATEGORY]->(c)
    """
    """Neo4j 合并子分类到主分类关系 Cypher"""

    NEO4J_MERGE_ARTICLE_TO_SUB_CATEGORY_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (a:Article {id: row.articleId})
        MATCH (s:SubCategory {id: row.subCategoryId})
        MERGE (a)-[:BELONGS_TO]->(s)
    """
    """Neo4j 合并文章到子分类关系 Cypher"""

    NEO4J_MERGE_PUBLISHED_BY_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (a:Article {id: row.articleId})
        MATCH (u:User {id: row.userId})
        MERGE (a)-[:PUBLISHED_BY]->(u)
    """
    """Neo4j 合并文章作者关系 Cypher"""

    NEO4J_MERGE_TAGGED_AS_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (a:Article {id: row.articleId})
        MATCH (t:Tag {name: row.tagName})
        MERGE (a)-[:TAGGED_AS]->(t)
    """
    """Neo4j 合并文章标签关系 Cypher"""

    NEO4J_MERGE_LIKES_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (u:User {id: row.userId})
        MATCH (a:Article {id: row.articleId})
        MERGE (u)-[r:LIKES]->(a)
        SET r.createdAt = row.createdAt
    """
    """Neo4j 合并点赞关系 Cypher"""

    NEO4J_MERGE_COLLECTS_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (u:User {id: row.userId})
        MATCH (a:Article {id: row.articleId})
        MERGE (u)-[r:COLLECTS]->(a)
        SET r.createdAt = row.createdAt
    """
    """Neo4j 合并收藏关系 Cypher"""

    NEO4J_MERGE_COMMENTED_ON_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (u:User {id: row.userId})
        MATCH (a:Article {id: row.articleId})
        MERGE (u)-[r:COMMENTED_ON {commentId: row.commentId}]->(a)
        SET r.createdAt = row.createdAt
    """
    """Neo4j 合并评论关系 Cypher"""

    NEO4J_MERGE_FOLLOWS_CYPHER: str = """
        UNWIND $rows AS row
        MATCH (u1:User {id: row.followerId})
        MATCH (u2:User {id: row.followedId})
        MERGE (u1)-[r:FOLLOWS]->(u2)
        SET r.createdAt = row.createdAt
    """
    """Neo4j 合并关注关系 Cypher"""

    NEO4J_CLEANUP_PUBLISHED_BY_CYPHER: str = """
        MATCH (a:Article)-[r:PUBLISHED_BY]->(u:User)
        WITH r, toString(a.id) + ':' + toString(u.id) AS relationKey
        WHERE NOT (relationKey IN $keys)
        DELETE r
    """
    """Neo4j 清理失效文章作者关系 Cypher"""

    NEO4J_CLEANUP_ARTICLE_SUB_CATEGORY_CYPHER: str = """
        MATCH (a:Article)-[r:BELONGS_TO]->(s:SubCategory)
        WITH r, toString(a.id) + ':' + toString(s.id) AS relationKey
        WHERE NOT (relationKey IN $keys)
        DELETE r
    """
    """Neo4j 清理失效文章子分类关系 Cypher"""

    NEO4J_CLEANUP_SUB_CATEGORY_CATEGORY_CYPHER: str = """
        MATCH (s:SubCategory)-[r:BELONGS_TO_CATEGORY]->(c:Category)
        WITH r, toString(s.id) + ':' + toString(c.id) AS relationKey
        WHERE NOT (relationKey IN $keys)
        DELETE r
    """
    """Neo4j 清理失效子分类主分类关系 Cypher"""

    NEO4J_CLEANUP_TAGGED_AS_CYPHER: str = """
        MATCH (a:Article)-[r:TAGGED_AS]->(t:Tag)
        WITH r, toString(a.id) + ':' + t.name AS relationKey
        WHERE NOT (relationKey IN $keys)
        DELETE r
    """
    """Neo4j 清理失效文章标签关系 Cypher"""

    NEO4J_CLEANUP_LIKES_CYPHER: str = """
        MATCH (u:User)-[r:LIKES]->(a:Article)
        WITH r, toString(u.id) + ':' + toString(a.id) AS relationKey
        WHERE NOT (relationKey IN $keys)
        DELETE r
    """
    """Neo4j 清理失效点赞关系 Cypher"""

    NEO4J_CLEANUP_COLLECTS_CYPHER: str = """
        MATCH (u:User)-[r:COLLECTS]->(a:Article)
        WITH r, toString(u.id) + ':' + toString(a.id) AS relationKey
        WHERE NOT (relationKey IN $keys)
        DELETE r
    """
    """Neo4j 清理失效收藏关系 Cypher"""

    NEO4J_CLEANUP_COMMENTED_ON_CYPHER: str = """
        MATCH (u:User)-[r:COMMENTED_ON]->(a:Article)
        WITH r, toString(r.commentId) + ':' + toString(u.id) + ':' + toString(a.id) AS relationKey
        WHERE NOT (relationKey IN $keys)
        DELETE r
    """
    """Neo4j 清理失效评论关系 Cypher"""

    NEO4J_CLEANUP_FOLLOWS_CYPHER: str = """
        MATCH (u1:User)-[r:FOLLOWS]->(u2:User)
        WITH r, toString(u1.id) + ':' + toString(u2.id) AS relationKey
        WHERE NOT (relationKey IN $keys)
        DELETE r
    """
    """Neo4j 清理失效关注关系 Cypher"""

    NEO4J_CLEANUP_ARTICLES_CYPHER: str = """
        MATCH (a:Article)
        WHERE NOT (a.id IN $ids)
        DETACH DELETE a
    """
    """Neo4j 清理失效文章节点 Cypher"""

    NEO4J_CLEANUP_USERS_CYPHER: str = """
        MATCH (u:User)
        WHERE NOT (u.id IN $ids)
        DETACH DELETE u
    """
    """Neo4j 清理失效用户节点 Cypher"""

    NEO4J_CLEANUP_SUB_CATEGORIES_CYPHER: str = """
        MATCH (s:SubCategory)
        WHERE NOT (s.id IN $ids)
        DETACH DELETE s
    """
    """Neo4j 清理失效子分类节点 Cypher"""

    NEO4J_CLEANUP_CATEGORIES_CYPHER: str = """
        MATCH (c:Category)
        WHERE NOT (c.id IN $ids)
        DETACH DELETE c
    """
    """Neo4j 清理失效主分类节点 Cypher"""

    NEO4J_CLEANUP_TAGS_CYPHER: str = """
        MATCH (t:Tag)
        WHERE NOT (t.name IN $names)
        DETACH DELETE t
    """
    """Neo4j 清理失效标签节点 Cypher"""

    INTENT_TO_CYPHER: Dict[str, str] = {
        "article_detail": """
            MATCH (a:Article {id: $id})
            OPTIONAL MATCH (a)-[:PUBLISHED_BY]->(u:User)
            OPTIONAL MATCH (a)-[:BELONGS_TO]->(s:SubCategory)
            OPTIONAL MATCH (s)-[:BELONGS_TO_CATEGORY]->(c:Category)
            OPTIONAL MATCH (a)-[:TAGGED_AS]->(t:Tag)
            RETURN a.id AS id, a.title AS title, a.views AS views,
                u.name AS author, s.name AS subCategory, c.name AS category,
                collect(DISTINCT t.name) AS tags
        """,
        "category_articles": """
            MATCH (s:SubCategory {name: $name})<-[:BELONGS_TO]-(a:Article)
            OPTIONAL MATCH (a)-[:PUBLISHED_BY]->(u:User)
            RETURN a.id AS id, a.title AS title, a.views AS views,
                a.createAt AS createAt, u.name AS author
            ORDER BY a.views DESC LIMIT $limit
        """,
        "user_articles": """
            MATCH (a:Article)-[:PUBLISHED_BY]->(u:User {name: $name})
            RETURN a.id AS id, a.title AS title, a.views AS views, a.createAt AS createAt
            ORDER BY a.createAt DESC LIMIT $limit
        """,
        "similar_articles_same_category": """
            MATCH (a:Article {id: $articleId})-[:BELONGS_TO]->(s:SubCategory)
            MATCH (other:Article)-[:BELONGS_TO]->(s)
            WHERE other.id <> a.id
            OPTIONAL MATCH (other)-[:PUBLISHED_BY]->(u:User)
            RETURN other.id AS id, other.title AS title, other.views AS views,
                u.name AS author
            ORDER BY other.views DESC LIMIT $limit
        """,
        "user_interest_chain": """
            MATCH (u:User {id: $userId})-[:FOLLOWS]->(:User)-[:LIKES]->(a:Article)
            OPTIONAL MATCH (a)-[:PUBLISHED_BY]->(author:User)
            RETURN a.id AS id, a.title AS title, a.views AS views, author.name AS author
            ORDER BY a.views DESC LIMIT $limit
        """,
        "top_viewed_articles": """
            MATCH (a:Article)
            RETURN a.id AS id, a.title AS title, a.views AS views
            ORDER BY a.views DESC LIMIT $limit
        """,
        "tag_graph": """
            MATCH (t:Tag)<-[:TAGGED_AS]-(a:Article)
            RETURN t.name AS tag, count(a) AS articleCount
            ORDER BY articleCount DESC LIMIT $limit
        """,
        "user_recommendation": """
            MATCH (u:User {id: $userId})-[:LIKES|COLLECTS]->(interest:Article)
            MATCH (interest)-[:TAGGED_AS]->(t:Tag)
            MATCH (a:Article)-[:TAGGED_AS]->(t)
            WHERE a.id <> interest.id
            AND NOT EXISTS { (u)-[:LIKES|COLLECTS]->(a) }
            OPTIONAL MATCH (a)-[:PUBLISHED_BY]->(author:User)
            RETURN a.id AS id, a.title AS title, author.name AS author,
                collect(DISTINCT t.name) AS matchTags,
                count(DISTINCT t) AS relevance
            ORDER BY relevance DESC, a.views DESC LIMIT $limit
        """,
    }

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

    NEO4J_GRAPH_COUNT_CYPHER: str = "MATCH (n) RETURN count(n) AS total LIMIT 1"
    """Neo4j 图谱节点数量查询 Cypher"""

    # Agent 相关提示词/描述/消息

    ROUTER_INTENT_PROMPT: str = """
        你是一个智能路由助手，需要判断用户的问题类型。

        分析用户问题，判断应该使用哪种方式处理：

        1. **database_query** - 需要查询数据库统计数据、获取记录列表、数据分析时选择
        - 关键词：多少、统计、列表、查询、总数、排行、最新、用户信息等
        - 示例：
            * "有多少篇文章？"
            * "最近发布的10篇文章"
            * "user_id为123的用户信息"
            * "各分类的文章数量统计"
            * "浏览量最高的文章"

        2. **article_search** - 需要搜索文章内容、技术知识、教程等时选择
        - 关键词：如何、怎么做、教程、学习、介绍、什么是、原理等
        - 示例：
            * "如何使用Python进行数据分析？"
            * "React Hooks的使用方法"
            * "什么是机器学习？"
            * "Docker容器化部署教程"
            * "数据库索引的原理"

        3. **log_analysis** - 需要查询系统日志、API日志、用户活动分析时选择
        - 关键词：日志、活动、请求记录、错误、追踪、统计访问等
        - 示例：
            * "最近的错误日志"
            * "用户活动统计"
            * "API请求记录"
            * "今天有哪些错误"

        4. **knowledge_query** - 需要查询知识图谱、实体关系、图结构推荐时选择
        - 关键词：知识图谱、图谱、关系、关联、相似文章、同分类推荐、标签排行、关注链推荐等
        - 示例：
            * "根据知识图谱推荐我可能喜欢的文章"
            * "这篇文章同分类下还有哪些热门文章"
            * "标签最多关联了哪些文章"
            * "用户关注的人点赞过哪些文章"

        5. **general_chat** - 简单问候、闲聊、不需要查询数据的问题
        - 示例：
            * "你好"
            * "今天天气怎么样"
            * "你能做什么"

        请只返回以下五个选项之一：database_query、article_search、log_analysis、knowledge_query、general_chat
    """
    """意图识别路由器提示词模板"""

    RAG_TOOL_NAME: str = "search_articles"
    """RAG工具名称"""

    RAG_TOOL_DESC: str = """
        使用RAG(检索增强生成)搜索相关文章。
        根据用户问题，在向量数据库中搜索最相关的文章内容。
        适用于回答关于文章内容、技术知识、教程等问题。
        参数格式: 用户的问题或关键词(字符串)
        示例: "如何使用Python进行数据分析"
        使用场景: 用户询问具体的技术问题、寻找相关文章、需要文章内容支持时使用。
    """
    """RAG工具描述"""

    EMBEDDING_CONFIG_INCOMPLETE_MESSAGE: str = (
        "Embedding配置不完整，请先配置 EMBEDDING_API_KEY 或 DASHSCOPE_API_KEY"
    )
    """Embedding配置不完整消息"""

    RAG_SERVICE_NOT_INITIALIZED_MESSAGE: str = "RAG服务未初始化，请检查 Embedding 配置"
    """RAG服务未初始化消息"""

    NEO4J_SERVICE_UNAVAILABLE_MESSAGE: str = "Neo4j 知识图谱服务暂不可用"
    """Neo4j 服务不可用消息"""

    NEO4J_CONFIG_NOT_INITIALIZED_MESSAGE: str = "Neo4j 连接参数未初始化，无法创建驱动"
    """Neo4j 连接参数未初始化消息"""

    NEO4J_LOOP_NOT_RUNNING_MESSAGE: str = (
        "当前没有运行中的事件循环，无法创建 Neo4j 异步驱动"
    )
    """Neo4j 事件循环缺失消息"""

    NEO4J_DRIVER_NOT_INITIALIZED_MESSAGE: str = "Neo4j 驱动未初始化，无法创建会话"
    """Neo4j 驱动未初始化消息"""

    NEO4J_CURRENT_LOOP_DRIVER_CLOSED_MESSAGE: str = "Neo4j 当前事件循环驱动已关闭"
    """Neo4j 当前事件循环驱动关闭消息"""

    NEO4J_DRIVER_CLOSED_MESSAGE: str = "Neo4j 驱动已关闭"
    """Neo4j 驱动关闭消息"""

    NEO4J_QUERY_TOOLS_INITIALIZED_MESSAGE: str = "Neo4j 查询工具初始化成功"
    """Neo4j 查询工具初始化成功消息"""

    NEO4J_NO_RESULT_MESSAGE: str = "未找到相关知识图谱结果"
    """Neo4j 查询无结果消息"""

    NEO4J_QUERY_EMPTY_MESSAGE: str = "查询未返回结果"
    """Neo4j 自定义查询无结果消息"""

    NEO4J_QUERY_NAME_INPUT_DESC: str = "预定义查询名称，可选值: "
    """Neo4j 预定义查询名称输入描述"""

    NEO4J_QUERY_PARAMS_INPUT_DESC: str = (
        '查询参数，例如 {"id": 1, "name": "人工智能", "limit": 10}'
    )
    """Neo4j 查询参数输入描述"""

    NEO4J_CUSTOM_CYPHER_INPUT_DESC: str = "只读 Cypher 查询语句"
    """Neo4j 自定义 Cypher 输入描述"""

    NEO4J_LABEL_USER: str = "用户"
    """Neo4j 同步用户标签文案"""

    NEO4J_LABEL_CATEGORY: str = "主分类"
    """Neo4j 同步主分类标签文案"""

    NEO4J_LABEL_SUB_CATEGORY: str = "子分类"
    """Neo4j 同步子分类标签文案"""

    NEO4J_LABEL_ARTICLE: str = "文章"
    """Neo4j 同步文章标签文案"""

    NEO4J_LABEL_TAG: str = "标签"
    """Neo4j 同步标签文案"""

    NEO4J_LABEL_SUB_CATEGORY_RELATION: str = "子分类-主分类关系"
    """Neo4j 同步子分类主分类关系文案"""

    NEO4J_LABEL_ARTICLE_SUB_CATEGORY_RELATION: str = "文章-子分类关系"
    """Neo4j 同步文章子分类关系文案"""

    NEO4J_LABEL_ARTICLE_AUTHOR_RELATION: str = "文章-作者关系"
    """Neo4j 同步文章作者关系文案"""

    NEO4J_LABEL_ARTICLE_TAG_RELATION: str = "文章-标签关系"
    """Neo4j 同步文章标签关系文案"""

    NEO4J_LABEL_LIKE_RELATION: str = "点赞关系"
    """Neo4j 同步点赞关系文案"""

    NEO4J_LABEL_COLLECT_RELATION: str = "收藏关系"
    """Neo4j 同步收藏关系文案"""

    NEO4J_LABEL_COMMENT_RELATION: str = "评论关系"
    """Neo4j 同步评论关系文案"""

    NEO4J_LABEL_FOLLOW_RELATION: str = "关注关系"
    """Neo4j 同步关注关系文案"""

    NEO4J_CLEANUP_LABEL_PUBLISHED_BY_RELATION: str = "失效文章作者关系"
    """Neo4j 清理文章作者关系文案"""

    NEO4J_CLEANUP_LABEL_ARTICLE_SUB_CATEGORY_RELATION: str = "失效文章子分类关系"
    """Neo4j 清理文章子分类关系文案"""

    NEO4J_CLEANUP_LABEL_SUB_CATEGORY_CATEGORY_RELATION: str = "失效子分类主分类关系"
    """Neo4j 清理子分类主分类关系文案"""

    NEO4J_CLEANUP_LABEL_TAGGED_AS_RELATION: str = "失效文章标签关系"
    """Neo4j 清理文章标签关系文案"""

    NEO4J_CLEANUP_LABEL_LIKE_RELATION: str = "失效点赞关系"
    """Neo4j 清理点赞关系文案"""

    NEO4J_CLEANUP_LABEL_COLLECT_RELATION: str = "失效收藏关系"
    """Neo4j 清理收藏关系文案"""

    NEO4J_CLEANUP_LABEL_COMMENT_RELATION: str = "失效评论关系"
    """Neo4j 清理评论关系文案"""

    NEO4J_CLEANUP_LABEL_FOLLOW_RELATION: str = "失效关注关系"
    """Neo4j 清理关注关系文案"""

    NEO4J_CLEANUP_LABEL_ARTICLE: str = "失效文章节点"
    """Neo4j 清理文章节点文案"""

    NEO4J_CLEANUP_LABEL_USER: str = "失效用户节点"
    """Neo4j 清理用户节点文案"""

    NEO4J_CLEANUP_LABEL_SUB_CATEGORY: str = "失效子分类节点"
    """Neo4j 清理子分类节点文案"""

    NEO4J_CLEANUP_LABEL_CATEGORY: str = "失效主分类节点"
    """Neo4j 清理主分类节点文案"""

    NEO4J_CLEANUP_LABEL_TAG: str = "失效标签节点"
    """Neo4j 清理标签节点文案"""

    NEO4J_READ_ONLY_LIMIT_MESSAGE: str = (
        "安全限制：Neo4j 工具只允许执行单条只读 Cypher 查询。"
    )
    """Neo4j 只读查询限制消息"""

    NEO4J_PREDEFINED_QUERY_TOOL_NAME: str = "execute_knowledge_graph_query"
    """Neo4j 预定义查询工具名称"""

    NEO4J_PREDEFINED_QUERY_TOOL_DESC: str = """
        执行预定义的 Neo4j 知识图谱查询。
        适用于文章详情、分类热门文章、作者文章、同分类相似文章、关注链推荐、热门文章、标签排行和个性化推荐。
        参数包含 query_name 和 params。优先使用预定义查询，limit 最大 50。
    """
    """Neo4j 预定义查询工具描述"""

    NEO4J_CUSTOM_CYPHER_TOOL_NAME: str = "execute_custom_cypher_query"
    """Neo4j 自定义 Cypher 查询工具名称"""

    NEO4J_CUSTOM_CYPHER_TOOL_DESC: str = """
        执行自定义只读 Cypher 查询。
        图谱包含 User、Article、Category、SubCategory、Tag 节点，以及 PUBLISHED_BY、BELONGS_TO、BELONGS_TO_CATEGORY、TAGGED_AS、LIKES、COLLECTS、COMMENTED_ON、FOLLOWS 关系。
        仅允许 MATCH、OPTIONAL MATCH、WITH、RETURN 或 CALL db.* 类型的只读查询。
    """
    """Neo4j 自定义 Cypher 查询工具描述"""

    SQL_TOOL_LIMIT: str = "安全限制：只允许执行SELECT查询语句"
    """SQL工具限制消息"""

    SQL_QUERY_MULTIPLE_STATEMENTS_ERROR: str = (
        "安全限制：SQL 工具只允许执行单条只读查询，禁止多语句执行。"
    )
    """SQL多语句限制消息"""

    SQL_QUERY_WRITE_OPERATION_ERROR: str = (
        "安全限制：检测到 SQL 包含写操作或锁表行为，只允许执行只读查询。"
    )
    """SQL写操作限制消息"""

    SQL_NATURAL_LANGUAGE_WRITE_BLOCK_MESSAGE: str = "安全限制：当前请求带有新增、修改、删除等数据库写操作意图。SQL 工具仅支持只读查询，请改为查询类问题。"
    """自然语言写操作意图拦截消息"""

    USER_RELATED_TABLE: List[str] = [
        "likes",
        "collects",
        "comments",
        "ai_history",
        "chat_messages",
    ]
    """用户相关表"""

    SQL_QUERY_NO_RES: str = "查询成功，但没有返回结果"
    """SQL查询成功无结果消息"""

    SQL_TABLE_TOOL_NAME: str = "get_table_schema"
    """SQL获取表结构工具名称"""

    SQL_TABLE_INPUT_DESC: str = "表名，留空则返回所有表"
    """SQL 表结构工具输入描述"""

    SQL_TABLE_TOOL_DESC: str = """
        获取MySQL数据库表结构信息。
        如果提供表名参数，返回该表的详细结构（列名、类型、主键、索引等）。
        如果不提供参数，返回所有表的列表和基本信息。
        参数格式: 表名(字符串)，如 'articles' 或 'users'，留空获取所有表。
        使用场景: 需要了解数据库结构、查询某表有哪些字段时使用。
    """
    """SQL获取表结构工具描述"""

    SQL_QUERY_TOOL_NAME: str = "execute_sql_query"
    """SQL查询工具名称"""

    SQL_QUERY_INPUT_DESC: str = "完整的只读 SQL 查询语句"
    """SQL 查询工具输入描述"""

    SQL_QUERY_TOOL_DESC: str = """
        执行只读SQL查询并返回结果。
        只允许单条只读语句，例如 SELECT/WITH/SHOW/DESC/DESCRIBE/EXPLAIN。
        不允许 INSERT/UPDATE/DELETE/DDL/锁表/多语句 等任何修改或高风险操作。
        返回最多20行数据，以表格形式展示。
        参数格式: 完整的只读SQL语句。
        示例: "SELECT * FROM articles WHERE status=1 LIMIT 10"
        使用场景: 需要查询系统数据、业务数据、统计分析、获取具体记录时使用。
        如果涉及大表或可能返回大量数据，必须主动加上时间范围、用户范围、状态条件或 LIMIT。
    """
    """SQL查询工具描述"""

    MONGODB_LIST_COLLECTIONS_TOOL_NAME: str = "list_mongodb_collections"
    """MongoDB 列表查询工具名称"""

    MONGODB_LIST_COLLECTIONS_TOOL_DESC: str = """
        列出 MongoDB 日志数据库中的所有 collection 及其基本信息。
        返回每个 collection 的记录数和样本字段，帮助确认可查询的数据集合。
        参数格式: 无参数。
        使用场景: 用户需要先了解日志库里有哪些 collection 以及大致字段结构时使用。
    """
    """MongoDB 列表查询工具描述"""

    MONGODB_QUERY_TOOL_NAME: str = "query_mongodb"
    """MongoDB 通用查询工具名称"""

    MONGODB_COLLECTION_NAME_INPUT_DESC: str = "collection 的名称"
    """MongoDB collection 名称输入描述"""

    MONGODB_FILTER_INPUT_DESC: str = "MongoDB 查询条件"
    """MongoDB 查询条件输入描述"""

    MONGODB_LIMIT_INPUT_DESC: str = "返回结果数量限制"
    """MongoDB 查询条数限制输入描述"""

    MONGODB_QUERY_TOOL_DESC: str = """
        MongoDB 日志查询工具，仅用于查询日志相关 collection。
        参数必须是 JSON 字符串，支持 collection_name、filter_dict、limit 三个字段。
        参数示例: {"collection_name": "api_logs", "limit": 10}
        使用场景: 已明确 collection 后，按条件查询 API 日志、错误日志、操作日志等数据时使用。
        如果日志量可能较大，必须加上时间范围、用户范围、状态条件或 limit。
    """
    """MongoDB 通用查询工具描述"""

    CONTENT_SUMMARIZE_PROMPT: str = """
        请对以下内容进行精要总结，提取关键信息和核心观点：

        原文内容：
        {content}

        要求：
        1. 总结长度控制在 {max_length} 字以内
        2. 提取核心要点和关键信息
        3. 保留最重要的细节
        4. 用清晰、凝练的语言表述
    """
    """内容总结提示词"""

    REFERENCE_BASED_EVALUATION_PROMPT: str = """
        请基于以下权威参考文本，对文章或内容进行评价。

        权威参考文本：
        {reference_content}

        请对以下内容进行评价，并给出评分：
        1. 给出简短的评价（100-200字），要求在评价中明确提及"参考权威文本"或"基于权威文本"等字眼
        2. 给出0-10分的评分（可以是小数）
        3. 请使用以下格式输出：
            评价内容：[你的评价，需包含参考权威文本的相关表述]
            评分：[你的评分]
        4. 评价内容中应清晰指出哪些观点与权威文本相符或不符

        待评价内容：
        {message}
    """
    """基于参考文本的评价提示词"""

    AGENT_PROMPT_TEMPLATE: str = """
        你是一个中文 AI 助手，负责查询数据库信息、搜索文章内容、分析系统日志和使用知识图谱分析实体关系。

        你可以直接调用绑定好的工具，不需要手写 Thought/Action/Observation 这种文本格式。

        规则：
        1. 需要查询数据时优先使用工具，不要凭空猜测。
        2. 数据库统计和业务数据查询优先使用 SQL 工具，并尽量加上时间范围、用户范围、状态条件或 limit。
        3. 查询数据库表结构时，先确认真实表名，再执行查询；例如用户表是 user，不是 users。
        4. 涉及文章、用户、分类、标签之间的关系、相似文章和推荐时，优先使用 Neo4j 知识图谱工具。
        5. MongoDB 工具只用于日志相关查询，查询前先确认 collection 名称。
        6. 最终回答必须使用中文，简洁明确。

        当前问题：{input}
    """
    """AI 助手的Agent提示词模板"""

    # 权限相关常量

    ROLE_ADMIN: str = "admin"
    """管理员权限名称"""

    ROLE_USER: str = "user"
    """用户权限名称"""

    # 图谱搜索增强 - Cypher 语句

    GRAPH_SEARCH_TAG_INTEREST_CYPHER: str = """
        MATCH (u:User {id: $userId})-[:LIKES|COLLECTS]->(:Article)-[:TAGGED_AS]->(t:Tag)
        WITH t.name AS tagName, count(*) AS weight
        MATCH (a:Article)-[:TAGGED_AS]->(t2:Tag {name: tagName})
        WHERE a.id IN $articleIds
        RETURN a.id AS articleId,
               collect(DISTINCT tagName) AS matchedTags,
               sum(weight) AS rawScore
    """
    """图谱搜索增强: 用户兴趣标签查询"""

    GRAPH_SEARCH_FOLLOWED_AUTHOR_CYPHER: str = """
        MATCH (u:User {id: $userId})-[:FOLLOWS]->(author:User)<-[:PUBLISHED_BY]-(a:Article)
        WHERE a.id IN $articleIds
        RETURN a.id AS articleId,
               collect(DISTINCT author.name) AS names,
               count(DISTINCT author) AS rawScore
    """
    """图谱搜索增强: 关注作者查询"""

    GRAPH_SEARCH_SAME_SUB_CATEGORY_CYPHER: str = """
        MATCH (u:User {id: $userId})-[:LIKES|COLLECTS|COMMENTED_ON]->(:Article)-[:BELONGS_TO]->(s:SubCategory)
        WITH s.id AS subCategoryId, s.name AS subCategoryName, count(*) AS weight
        MATCH (a:Article)-[:BELONGS_TO]->(:SubCategory {id: subCategoryId})
        WHERE a.id IN $articleIds
        RETURN a.id AS articleId,
               collect(DISTINCT subCategoryName) AS names,
               sum(weight) AS rawScore
    """
    """图谱搜索增强: 同子分类查询"""

    GRAPH_SEARCH_CANDIDATE_SIMILARITY_CYPHER: str = """
        MATCH (a:Article)-[:TAGGED_AS]->(t:Tag)<-[:TAGGED_AS]-(other:Article)
        WHERE a.id IN $articleIds
          AND other.id IN $articleIds
          AND a.id <> other.id
        RETURN a.id AS articleId,
               collect(DISTINCT t.name) AS names,
               count(DISTINCT t) AS rawScore
    """
    """图谱搜索增强: 候选间相似标签查询"""

    GRAPH_SEARCH_KEYWORD_TAG_CYPHER: str = """
        MATCH (a:Article)-[:TAGGED_AS]->(t:Tag)
        WHERE a.id IN $articleIds
          AND $keyword <> ''
          AND toLower(t.name) CONTAINS toLower($keyword)
        RETURN a.id AS articleId,
               collect(DISTINCT t.name) AS names,
               count(DISTINCT t) AS rawScore
    """
    """图谱搜索增强: 关键词标签命中查询"""

    # 图谱搜索增强 - 关系原因

    GRAPH_SEARCH_REASON_INTEREST: str = "命中兴趣标签"
    """图谱搜索增强: 兴趣标签关系原因"""

    GRAPH_SEARCH_REASON_FOLLOWED: str = "来自你关注的作者"
    """图谱搜索增强: 关注作者关系原因"""

    GRAPH_SEARCH_REASON_SUB_CATEGORY: str = "属于你常看的分类"
    """图谱搜索增强: 同分类关系原因"""

    GRAPH_SEARCH_REASON_CANDIDATE: str = "与当前搜索结果中的多篇文章标签相关"
    """图谱搜索增强: 候选相似关系原因"""

    GRAPH_SEARCH_REASON_KEYWORD: str = "命中图谱标签"
    """图谱搜索增强: 关键词标签关系原因"""

    # 图谱搜索增强 - 路径描述

    GRAPH_SEARCH_PATH_INTEREST: str = "User-LIKES-Article-TAGGED_AS-Tag"
    """图谱搜索增强: 兴趣标签路径"""

    GRAPH_SEARCH_PATH_FOLLOWED: str = "User-FOLLOWS-User-PUBLISHED_BY-Article"
    """图谱搜索增强: 关注作者路径"""

    GRAPH_SEARCH_PATH_SUB_CATEGORY: str = (
        "User-LIKES|COLLECTS|COMMENTED_ON-Article-BELONGS_TO-SubCategory"
    )
    """图谱搜索增强: 同分类路径"""

    GRAPH_SEARCH_PATH_CANDIDATE: str = "Article-TAGGED_AS-Tag-TAGGED_AS-Article"
    """图谱搜索增强: 候选相似路径"""

    GRAPH_SEARCH_PATH_KEYWORD: str = "Article-TAGGED_AS-Tag"
    """图谱搜索增强: 关键词标签路径"""

    # 图谱搜索增强 - 日志消息

    GRAPH_SEARCH_QUERY_EXCEPTION_LOG: str = "图谱信号查询异常: {}"
    """图谱搜索增强: 信号查询异常日志"""

    GRAPH_SEARCH_NEO4J_EXCEPTION_LOG: str = "Neo4j 查询异常: {}"
    """图谱搜索增强: Neo4j 查询异常日志"""

    # 向量搜索增强 - 语义原因

    VECTOR_SEARCH_REASON_HIGH: str = "语义内容与搜索词高度相关"
    """向量搜索增强: 高相关原因"""

    VECTOR_SEARCH_REASON_MEDIUM: str = "语义内容与搜索词较相关"
    """向量搜索增强: 较相关原因"""

    VECTOR_SEARCH_REASON_LOW: str = "语义内容与搜索词存在相关性"
    """向量搜索增强: 低相关原因"""

    # Swagger 标签描述

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
    """OpenAPI 标签描述，用于在 Swagger 文档中展示各模块描述信息"""
