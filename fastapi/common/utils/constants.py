from typing import List


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
    
    STREAMING_CHAT_THINKING_SYSTEM_MESSAGE: str = "你是一个中文AI思考型助手，用于提供文章和博客推荐及分析系统数据的思考内容，回答文本应该展示的是调用工具和分析的思考过程。"
    """流式聊天思考过程系统消息"""
    
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
    
    SWAGGER_TITLE: str = "FastAPI部分的Swagger文档"
    """Swagger 文档标题"""
    
    SWAGGER_DESCRIPTION: str = "这是项目的FastAPI部分的Swagger文档"
    """Swagger 文档描述"""
    
    SWAGGER_VERSION: str = "1.0.0"
    """Swagger 文档版本"""
    
    STARTUP_MESSAGE: str = "FastAPI应用已启动"
    """启动消息"""
    
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
    
    L2_CACHE_UPDATED: str = "[L2缓存] Redis 已更新"
    """L2缓存更新消息"""
    
    L2_CACHE_CLEARED: str = "[L2缓存] Redis 已清除"
    """L2缓存清除消息"""
    
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
    
    RABBITMQ_CREATE_QUEUES_FAILURE_MESSAGE: str = "无法创建队列：RabbitMQ未连接"
    """无法创建队列消息"""
    
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

    USER_NOT_EXISTS_ERROR: str = "用户不存在"
    """用户不存在错误消息"""
    
    HIVE_QUERY = "从 Hive 查询"
    """Hive 查询消息"""
    
    UNKNOWN_ARTICLE = "未知文章"
    """未知文章消息"""
    
    GET_TOP_FAIL = "获取文章浏览分布失败"
    """获取文章浏览分布失败消息"""
    
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
    
    ARTICLE_COLUMN : str = [
        "id", "title", "tags", "status", "views", "create_at", "update_at", 
        "content", "user_id", "sub_category_id", "username"
    ]
    """文章表字段常量"""
    
    CATEGORY_ARTICLE_DISTRIBUTION_SQL: str = """
        SELECT sub_category_id, COUNT(*) as count
        FROM articles
        WHERE status = 1
        GROUP BY sub_category_id
        ORDER BY count DESC
    """
    """分类文章分布SQL"""
    
    MONTHLY_ARTICLE_PUBLISH_SQL: str = """
        SELECT substr(create_at, 1, 7) as year_month, COUNT(*) as count
        FROM articles
        WHERE status = 1
        AND create_at >= date_sub(current_date(), 730)
        GROUP BY substr(create_at, 1, 7)
        ORDER BY year_month DESC
    """
    """按月文章发布统计SQL"""
    
    SQL_QUERY_PREFIX: str = "SELECT"
    """SQL查询前缀"""
    
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

        4. **general_chat** - 简单问候、闲聊、不需要查询数据的问题
        - 示例：
            * "你好"
            * "今天天气怎么样"
            * "你能做什么"

        请只返回以下四个选项之一：database_query、article_search、log_analysis、general_chat
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
    
    SQL_TOOL_LIMIT: str = "安全限制：只允许执行SELECT查询语句"
    """SQL工具限制消息"""
    
    USER_RELATED_TABLE: List[str] = ['likes', 'collects', 'comments', 'ai_history', 'chat_messages']
    """用户相关表"""
    
    SQL_QUERY_NO_RES: str = "查询成功，但没有返回结果"
    """SQL查询成功无结果消息"""
    
    SQL_TABLE_TOOL_NAME: str = "get_table_schema"
    """SQL获取表结构工具名称"""
    
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
    
    SQL_QUERY_TOOL_DESC: str = """
        执行SQL SELECT查询并返回结果。
        只能执行SELECT查询，不允许INSERT/UPDATE/DELETE等修改操作。
        返回最多20行数据，以表格形式展示。
        参数格式: 完整的SQL SELECT语句。
        示例: "SELECT * FROM articles WHERE status=1 LIMIT 10"
        使用场景: 需要查询数据库数据、统计分析、获取具体记录时使用。
    """
    """SQL查询工具描述"""

    MONGODB_LIST_COLLECTIONS_TOOL_NAME: str = "list_mongodb_collections"
    """MongoDB 列表查询工具名称"""

    MONGODB_LIST_COLLECTIONS_TOOL_DESC: str = """
        列出 MongoDB 数据库中的所有 collection 及其基本信息。
        返回每个 collection 的记录数和样本字段，帮助确认可查询的数据集合。
        参数格式: 无参数。
        使用场景: 用户需要先了解日志库里有哪些 collection 以及大致字段结构时使用。
    """
    """MongoDB 列表查询工具描述"""

    MONGODB_QUERY_TOOL_NAME: str = "query_mongodb"
    """MongoDB 通用查询工具名称"""

    MONGODB_QUERY_TOOL_DESC: str = """
        通用的 MongoDB 查询工具，可查询任意 collection。
        参数必须是 JSON 字符串，支持 collection_name、filter_dict、limit 三个字段。
        参数示例: {"collection_name": "api_logs", "limit": 10}
        使用场景: 已明确 collection 后，按条件查询日志、错误记录、用户活动等数据时使用。
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
        你是一个智能助手，可以帮助用户查询数据库信息、搜索文章内容和分析系统日志。

        你有以下工具可以使用:
        {tools}

        工具名称: {tool_names}

        使用以下格式回答问题:

        Question: 用户的问题
        Thought: 你需要思考应该做什么
        Action: 选择一个工具，必须是 [{tool_names}] 中的一个
        Action Input: 工具的输入参数
        Observation: 工具执行的结果
        ... (这个 Thought/Action/Action Input/Observation 可以重复N次)
        Thought: 我现在知道最终答案了
        Final Answer: 给用户的最终回答

        重要提示 - 如何选择和使用工具:

        1. 数据统计/统计查询: 优先使用 get_table_schema 查看表结构，然后用 execute_sql_query 执行SQL查询
        示例: "有多少篇文章"、"发布最多的作者是谁"、"文章总浏览量"

        2. 文章内容/技术知识查询: 使用 search_articles 搜索相关文章
        示例: "Python最佳实践"、"如何学习机器学习"、"深度学习教程"

        3. MongoDB 日志和系统分析: 使用以下两个工具

        第一步: 使用 list_mongodb_collections 列出所有可用的 collection
        - 这会告诉你有哪些数据集合可以查询（如 api_logs, error_logs 等）
        - 以及每个 collection 中有哪些字段
        - Action Input: (无需参数)

        第二步: 使用 query_mongodb 查询特定 collection
        Action Input 必须是 JSON 格式字符串，包含以下参数:
        - collection_name: 必需，collection 的名称 (字符串)
        - filter_dict: 可选，MongoDB 查询条件 (JSON对象)
        - limit: 可选，返回结果数量限制 (整数，默认10)
        
        Action Input 示例:
        - 查询 api_logs 的前10条: {{"collection_name": "api_logs", "limit": 10}}
        - 查询特定用户的 api_logs: {{"collection_name": "api_logs", "filter_dict": {{"user_id": 122}}, "limit": 20}}
        - 查询错误日志: {{"collection_name": "error_logs", "limit": 10}}
        - 查询文章日志: {{"collection_name": "articlelogs", "limit": 10}}

        4. 工作流程建议:
        - 如果用户问关于"日志"、"记录"、"API请求"、"错误"等：
            1) 首先调用 list_mongodb_collections 查看有哪些 collection
            2) 然后根据结果调用 query_mongodb 查询具体数据
        
        - 对于简单查询（如"最近的API请求"）：
            直接使用 query_mongodb，传递 JSON 参数

        关键特点:
        - 你可以根据需要多次使用工具
        - 对于组合问题，分步骤调用不同的工具
        - 始终用中文回答用户
        - MongoDB 的 filter_dict 支持完整的 MongoDB 查询语法，如 $gte, $lte, $regex 等
        - 如果查询返回空结果，可以尝试修改查询条件或查询其他 collection
        - Action Input 必须是有效的 JSON 字符串，不能是 Python 字典

        开始!

        Question: {input}
        Thought: {agent_scratchpad}
    """
    """AI 助手的Agent提示词模板"""

    # 权限相关常量
    
    ROLE_ADMIN: str = "admin"
    """管理员权限名称"""
    
    ROLE_USER: str = "user"
    """用户权限名称"""