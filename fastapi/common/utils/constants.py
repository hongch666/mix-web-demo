class Constants:
    """应用常量类"""
    
    TEST_MESSAGE: str = "Hello, I am FastAPI!"
    """FastAPI 测试消息"""
    
    VECTOR_SYNC_COMPLETE: str = "文章内容 hash 缓存初始化完成"
    """向量数据库同步完成消息"""
    
    AI_COMMENT_TASK_SUBMITTED: str = "AI生成评论任务已提交"
    """AI生成评论任务提交消息"""
    
    AI_COMMENT_WITH_REFERENCE_TASK_SUBMITTED: str = "基于权威参考文本的AI生成评论任务已提交"
    """基于权威参考文本的AI生成评论任务提交消息"""
    
    REQUEST_PROCESSING: str = "请求正在处理中"
    """请求处理中消息"""
    
    TOP10_CACHE_MISS: str = "get_top10_articles_service: [缓存未命中] 开始查询数据源"
    """TOP10文章缓存未命中消息"""
    
    TOP10_HIVE_SOURCE: str = "get_top10_articles_service: 使用 Hive 数据源"
    """TOP10文章使用Hive数据源消息"""
    
    TOP10_SPARK_SOURCE: str = "get_top10_articles_service: 使用 Spark 数据源"
    """TOP10文章使用Spark数据源消息"""
    
    TOP10_DB_SOURCE: str = "get_top10_articles_service: 使用 DB 数据源"
    """TOP10文章使用DB数据源消息"""
    
    KEYWORDS_EMPTY: str = "关键词字典为空，无法生成词云图"
    """关键词字典为空消息"""
    
    WORDCLOUD_FILENAME: str = "search_keywords_wordcloud.png"
    """词云图文件名"""
    
    WORDCLOUD_GENERATION_SUCCESS: str = "词云图生成成功，保存为 search_keywords_wordcloud.png"
    """词云图生成成功消息"""
    
    WORDCLOUD_CACHE_FETCH_FAILED: str = "get_wordcloud_service: [缓存未命中] 开始生成词云图"
    """词云图缓存获取失败消息"""
    
    EXPORT_ARTICLES_EXCEL_TIP: str = "文章表（本表导出自系统，包含所有文章数据）"
    """文章表导出Excel提示信息"""
    
    EXPORT_ARTICLES_EXCEL_FILENAME: str = "articles.xlsx"
    """文章表导出Excel文件名"""
    
    EXPORT_ARTICLES_EXCEL_OSS_PATH: str = "excel/articles.xlsx"
    """文章表导出Excel表OSS路径"""
    
    STATISTICS_CACHE_FETCH_FAILED: str = "get_article_statistics_service: [缓存未命中] 开始查询数据源"
    """文章统计信息缓存未命中消息"""
    
    CATEGORY_STATISTICS_CACHE_FETCH_FAILED: str = "get_category_article_count_service: [缓存未命中] 开始查询数据源"
    """分类文章统计缓存未命中消息"""
    
    CATEGORY_STATISTICS_HIVE_SOURCE: str = "get_category_article_count_service: 使用 Hive 数据源"
    """分类文章统计使用Hive数据源消息"""
    
    CATEGORY_STATISTICS_SPARK_SOURCE: str = "get_category_article_count_service: 使用 Spark 数据源"
    """分类文章统计使用Spark数据源消息"""
    
    CATEGORY_STATISTICS_DB_SOURCE: str = "get_category_article_count_service: 使用 DB 数据源"
    """分类文章统计使用DB数据源消息"""
    
    MONTHLY_STATISTICS_CACHE_FETCH_FAILED: str = "get_monthly_publish_count_service: [缓存未命中] 开始查询数据源"
    """月度文章统计缓存未命中消息"""
    
    MONTHLY_STATISTICS_HIVE_SOURCE: str = "get_monthly_publish_count_service: 使用 Hive 数据源"
    """月度文章统计使用Hive数据源消息"""
    
    MONTHLY_STATISTICS_SPARK_SOURCE: str = "get_monthly_publish_count_service: 使用 Spark 数据源"
    """月度文章统计使用Spark数据源消息"""
    
    MONTHLY_STATISTICS_DB_SOURCE: str = "get_monthly_publish_count_service: 使用 DB 数据源"
    """月度文章统计使用DB数据源消息"""
    
    DOUBAO_AGENT_INITIALIZATION_SUCCESS: str = "豆包Agent服务初始化完成"
    """豆包Agent初始化成功"""
    
    DOUBAO_CONFIGURATION_INCOMPLETE_ERROR: str = "豆包配置不完整，客户端未初始化"
    """豆包配置不完整错误消息"""
    
    INITIALIZATION_ERROR: str = "聊天服务未配置或初始化失败"
    """初始化错误消息"""
    
    GENERIC_CHAT_MESSAGE: str = "你是一个中文AI助手，用于提供文章和博客推荐及分析系统数据。"
    """普通系统消息"""
    
    REFERENCE_CHAT_MESSAGE: str = "你是一个专业的文章评价助手。请根据提供的权威参考文本进行客观、专业的评价。"
    """基于参考文本的聊天系统消息"""
    
    SUMMARIZE_CHAT_MESSAGE: str = "你是一个专业的内容总结助手。请精准提取核心信息，用凝练的语言进行总结。"
    """总结功能的系统消息"""
    
    CHAT_SYSTEM_MESSAGE: str = "你是一个中文AI助手，用于提供文章和博客推荐及分析系统数据。"
    """聊天功能的系统消息"""
    
    AGENT_PROCESSING_MESSAGE: str = "使用Agent处理，可同时调用SQL和RAG工具"
    """Agent处理消息"""
    
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
    
    GEMINI_QUOTA_EXCEEDED_ERROR: str = "Gemini API 配额已用完。建议切换到豆包或通义千问服务。"
    """Gemini配额用尽消息"""
    
    GEMINI_RATE_LIMIT_EXCEEDED_ERROR: str = "Gemini API调用频率超限。请稍后重试。"
    """Gemini调用频率超限消息"""
    
    REQUEST_TIMEOUT_ERROR: str = "请求超时，请稍后重试。"
    """请求超时错误消息"""
    
    QWEN_AGENT_INITIALIZATION_SUCCESS: str = "Qwen Agent服务初始化完成"
    """Qwen Agent初始化成功"""
    
    QWEN_CONFIGURATION_INCOMPLETE_ERROR: str = "Qwen配置不完整，客户端未初始化"
    """Qwen配置不完整错误消息"""
    
    QWEN_INVALID_API_KEY_ERROR: str = "API密钥无效。请检查Qwen API密钥配置。"
    """Qwen密钥无效消息"""
    
    QWEN_QUOTA_EXCEEDED_ERROR: str = "Qwen API 配额已用完。建议切换到豆包或通义千问服务。"
    """Qwen配额用尽消息"""
    
    QWEN_RATE_LIMIT_EXCEEDED_ERROR: str = "Qwen API调用频率超限。请稍后重试。"
    """Qwen调用频率超限消息"""
    
    DOUBAO_CALL_FAILED_ERROR: str = "豆包调用失败"
    """豆包调用失败消息"""
    
    GEMINI_CALL_FAILED_ERROR: str = "Gemini调用失败"
    """Gemini调用失败消息"""
    
    QWEN_CALL_FAILED_ERROR: str = "Qwen调用失败"
    """Qwen调用失败消息"""
    
    CATEGORY_NO_AUTHORITATIVE_REFERENCE_TEXT_ERROR: str = "该分类暂无权威参考文本，请根据您的专业知识进行评价。"
    """分类无权威参考文本错误消息"""
    
    REFERENCE_TEXT_EXTRACTION_ERROR: str = "无法提取参考文本"
    """无法提取参考文本错误消息"""
    
    CONCURRENT_SUMMARY_MESSAGE: str = "开始并发调用三个大模型进行总结"
    """并发总结消息"""
    
    CONCURRENT_CHAT_MESSAGE_SUCCESS: str = "权威文章生成完成，所有大模型总结已完成"
    """并发聊天完成消息"""
    
    SWAGGER_TITLE: str = "FastAPI部分的Swagger文档集成"
    """Swagger 文档标题"""
    
    SWAGGER_DESCRIPTION: str = "这是demo项目的FastAPI部分的Swagger文档集成"
    """Swagger 文档描述"""
    
    SWAGGER_VERSION: str = "1.0.0"
    """Swagger 文档版本"""
    
    INTENT_ROUTER_NO_PERMISSION_ERROR: str = "权限拒绝：此功能需要登录后才能使用。请先登录您的账户。您可以继续使用文章搜索和闲聊功能。"
    """意图识别权限拒绝信息"""
    
    COLLECTION_NAME_VALIDATION_ERROR: str = "错误: 必须提供 collection_name 参数"
    """collection_name参数验证错误消息"""
    
    RECURSIVE_URL_LOADER_NO_HEADER_SUPPORT: str = "RecursiveUrlLoader 不支持 headers 参数，使用基础版本"
    """RecursiveUrlLoader不支持header参数"""
    
    RECURSIVE_URL_LOADER_MESSAGE: str = "正在递归抓取页面，这可能需要一些时间..."
    """递归抓取页面消息"""
    
    EMPTY_CONTENT_MESSAGE: str = "（空内容）"
    """空内容消息"""
    
    REQUEST_DEPRECATION_MESSAGE: str = "使用 requests 库作为降级方案获取链接内容..."
    """request库降级提示消息"""
    
    URLLIB_DEPRECATION_MESSAGE: str = "requests 库未安装，尝试 urllib 降级方案"
    """urllib降级提示消息"""
    
    USING_URLLIB_DEPRECATION_MESSAGE: str = "使用 urllib 作为最后降级方案获取链接内容..."
    """使用urllib库降级提示消息"""
    
    TEXT_SPLITTER_INITIALIZATION_SUCCESS: str = "文本切分器初始化成功"
    """文本切分器初始化"""
    
    VECTOR_STORE_INITIALIZATION_SUCCESS: str = "PostgreSQL向量存储初始化成功"
    """向量存储初始化成功消息"""
    
    NO_RELEVANT_ARTICLES_FOUND_MESSAGE: str = "未找到相关文章。可能没有匹配的内容或相似度不足。请提供更具体的查询词或重新表述问题。"
    """未找到相关文章提示消息"""
    
    SQL_TOOL_INITIALIZATION_SUCCESS: str = "SQL工具初始化成功"
    """SQL工具初始化成功消息"""
    
    DEFAULT_KEYWORDS: str = [
        "我的", "个人", "自己的", "本人的", "我", "自己",
        "点赞", "收藏", "喜欢", "评论", "互动", "关注"
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
    
    HIVE_CACHE_MISS_QUERY_HIVE_MESSAGE: str = "[缓存] L1/L2 都未命中，需要查询 Hive"
    """缓存未命中查询Hive消息"""
    
    L1_CACHE_UPDATED: str = "[L1缓存] 已更新"
    """L1缓存更新消息"""
    
    L1_CACHE_CLEARED: str = "[L1缓存] 已清除"
    """L1缓存清除消息"""
    
    L2_CACHE_UPDATED: str = "[L2缓存] Redis 已清除"
    """L2缓存更新消息"""
    
    REDIS_CACHE_CLEARED: str = "Redis客户端未初始化，跳过缓存"
    """Redis缓存未初始化消息"""
    
    WORDCLOUD_CACHE_MISS: str = "词云图缓存未命中"
    """词云图缓存未命中消息"""
    
    WORDCLOUD_CACHE_DELETED: str = "词云图缓存已删除"
    """词云图缓存删除消息"""
    
    RABBITMQ_LOGGING_FAILURE: str = "RabbitMQ 客户端不可用，API 日志将不会发送到队列"
    """RabbitMQ 不可用导致API日志记录失败消息"""
    
    RABBITMQ_NOT_AVAILABLE: str = "日志装饰器捕获到异常，请检查日志详情";
    """日志装饰器异常捕获消息"""
    
    API_RABBITMQ_LOGGING_SUCCESS: str = "API 日志已发送到队列"
    """API日志消息发送成功消息"""
    
    API_RABBITMQ_LOGGING_FAILURE: str = "API 日志发送到队列失败"
    """API日志消息发送失败消息"""
    
    EXCEPTION_HANDLER_MESSAGE: str = "FastAPI服务器错误"
    """异常处理统一消息"""
    
    HIVE_CONNECTION_POOL_FULL_MESSAGE: str = "[连接池] 池已满，关闭连接"
    """Hive 连接池满消息"""
    
    AI_CHAT_TABLE_CREATION_MESSAGE: str = "ai_history 表创建完成"
    """表创建完成消息"""
    
    AI_CHAT_TABLE_EXISTS_MESSAGE: str = "ai_history 表已存在"
    """表已存在消息"""
    
    AI_CHAT_TABLE_UNSUPPORTED_MESSAGE: str = "仅支持创建 ai_history 表"
    """仅支持创建 ai_history 表消息"""
    
    AI_CHAT_NO_INSTANCE_MESSAGE: str = "找不到可用的服务实例"
    """找不到实例消息"""
    
    OSS_FILE_UPLOAD_START_MESSAGE: str = "开始上传文件到OSS"
    """开始上传阿里云OSS文件消息"""
    
    RABBITMQ_CLIENT_NOT_INITIALIZED_MESSAGE: str = "RabbitMQ 客户端未初始化，无法发送消息到队列"
    """RabbitMQ客户端未初始化消息"""
    
    RABBITMQ_CONFIG_NOT_FOUND_MESSAGE: str = "RabbitMQ 配置不存在，跳过连接"
    """RabbitMQ配置不存在消息"""
    
    RABBITMQ_NOT_CONNECTED_MESSAGE: str = "RabbitMQ 未连接，无法发送消息"
    """RabbitMQ未连接消息"""
    
    RABBITMQ_CONNECTION_CLOSED_MESSAGE: str = "RabbitMQ 连接已关闭"
    """RabbitMQ连接关闭消息"""
    
    REDIS_DATABASE_CLEARED_MESSAGE: str = "Redis数据库已清空"
    """Redis数据库已清空消息"""
    
    UPDATE_ANALYZE_CACHES_ANALYZE_SERVICE_NONE_MESSAGE: str = "update_analyze_caches: analyze_service 为 None，跳过缓存更新"
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
    
    UPDATE_ANALYZE_CACHES_CATEGORY_STATISTICS_START_MESSAGE: str = "更新按分类统计文章数量缓存..."
    """更新按分类统计文章数量缓存开始消息"""
    
    UPDATE_ANALYZE_CACHES_CATEGORY_STATISTICS_SUCCESS_MESSAGE: str = "按分类统计文章数量缓存更新成功"
    """按分类统计文章数量缓存更新成功消息"""
    
    UPDATE_ANALYZE_CACHES_MONTHLY_STATISTICS_START_MESSAGE: str = "更新月度文章发布统计缓存..."
    """更新月度文章发布统计缓存开始消息"""
    
    UPDATE_ANALYZE_CACHES_MONTHLY_STATISTICS_SUCCESS_MESSAGE: str = "月度文章发布统计缓存更新成功"
    """月度文章发布统计缓存更新成功消息"""
    
    UPDATE_ANALYZE_CACHES_COMPLETE_MESSAGE: str = "分析接口缓存更新完成"
    """分析接口缓存更新完成消息"""
    
    ARTICLE_MAPPER_NO_GET_ALL_METHOD_ERROR: str = "article_mapper 未提供获取全部文章的方法"
    """article_mapper 未提供获取全部文章的方法错误消息"""
    
    NO_TEXT_CONTENT_AVAILABLE_MESSAGE: str = "没有文章数据可导出"
    """没有文字内容可导出的提示信息"""
    
    HIVE_TABLE_CREATED_MESSAGE: str = "hive表已创建"
    """Hive表已创建消息"""
    
    CACHES_CLEARED_MESSAGE: str = "已清除所有缓存: top10文章、分类文章数、月份文章数、统计信息"
    """已清除所有缓存消息"""
    
    SCHEDULER_STARTED_MESSAGE: str = "定时任务调度器已启动："
    """调度器启动消息"""
    
    SCHEDULER_TASKS_MESSAGE: str = "  - 文章导出任务：每 1 天执行一次（包含缓存清理）"
    """调度器文章导出任务消息"""
    
    SCHEDULER_VECTOR_SYNC_MESSAGE: str = "  - 向量同步任务：每 1 天执行一次"
    """调度器向量同步任务消息"""
    
    SCHEDULER_ANALYZE_CACHE_UPDATE_MESSAGE: str = "  - 分析接口缓存更新任务：每 10 分钟执行一次（启动时立即执行）"
    """调度器分析接口缓存更新任务消息"""
    
    NO_ARTICLES_DATA_MESSAGE: str = "没有文章数据"
    """没有文章数据消息"""
    
    NO_CHANGED_ARTICLES_MESSAGE: str = "没有文章内容变更，跳过向量库同步"
    """没有文章内容变更消息"""
    
    NO_PUBLISHED_ARTICLES_MESSAGE: str = "没有已发布的文章需要同步"
    """没有已发布的文章需要同步消息"""
    
    START_INITIALIZING_ARTICLE_HASH_CACHE_MESSAGE: str = "开始初始化文章内容 hash 缓存..."
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
    
    CSV_LOADED_TO_HIVE_MESSAGE: str = "CSV 文件已加载到 Hive"
    """CSV 文件加载到 Hive 完成消息"""
    
    DB_CACHE_MISS_QUERY_DB_MESSAGE: str = "[缓存] L1/L2 都未命中，需要查询 DB"
    """缓存未命中查询DB消息"""
    
    USER_NOT_LOGGED_IN_MESSAGE: str = "用户未登录，请先登录"
    """用户未登录消息"""
    
    USER_NO_ADMIN_PERMISSION_MESSAGE: str = "权限不足，仅管理员可访问"
    """权限不足消息"""
    
    PERMISSION_CHECK_FAILED_MESSAGE: str = "权限检查失败"
    """权限检查失败消息"""
    
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
    
    HIVE_TABLE_VERSION_SQL: str = "SHOW TBLPROPERTIES articles"
    """获取Hive表的版本号SQL"""
    