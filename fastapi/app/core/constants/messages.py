from typing import Any, List, Optional


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

    @staticmethod
    def STARTUP_SERVICE_ADDRESS(ip: str, port: int) -> str:
        return f"服务地址:http://{ip}:{port}"

    @staticmethod
    def STARTUP_SWAGGER_ADDRESS(ip: str, port: int) -> str:
        return f"Swagger文档地址: http://{ip}:{port}/docs"

    @staticmethod
    def STARTUP_REDOC_ADDRESS(ip: str, port: int) -> str:
        return f"ReDoc文档地址: http://{ip}:{port}/redoc"

    @staticmethod
    def LLM_INITIALIZATION_SUCCESS(service_name: str) -> str:
        return f"{service_name} Agent服务初始化完成"

    @staticmethod
    def LLM_CONFIGURATION_INCOMPLETE(service_name: str) -> str:
        return f"{service_name}配置不完整，客户端未初始化"

    @staticmethod
    def LLM_CLIENT_INITIALIZATION_FAILED(service_name: str, error: Exception) -> str:
        return f"初始化{service_name}客户端失败: {error}"

    @staticmethod
    def LLM_INVALID_API_KEY(service_name: str) -> str:
        return f"API密钥无效。请检查{service_name} API密钥配置。"

    @staticmethod
    def LLM_QUOTA_EXCEEDED(service_name: str) -> str:
        return f"{service_name} API 配额已用完。请稍后重试。"

    @staticmethod
    def LLM_RATE_LIMIT_EXCEEDED(service_name: str) -> str:
        return f"{service_name} API调用频率超限。请稍后重试。"

    @staticmethod
    def LLM_CALL_FAILED(service_name: str) -> str:
        return f"{service_name}调用失败"

    @staticmethod
    def LLM_SERVICE_ERROR(service_name: str, error_message: str) -> str:
        return f"{service_name}服务异常: {error_message}"

    @staticmethod
    def CHAT_SERVICE_ERROR(error: Exception) -> str:
        return f"对话服务异常: {error}"

    @staticmethod
    def SUMMARIZE_SERVICE_ERROR(error: Exception) -> str:
        return f"总结服务异常: {error}"

    @staticmethod
    def ADMIN_PERMISSION_DENIED(user_id: str, user_role: str) -> str:
        return f"权限不足: 用户 {user_id} 尝试访问管理员接口，角色: {user_role}"

    @staticmethod
    def ADMIN_ACCESS_GRANTED(user_id: str) -> str:
        return f"管理员 {user_id} 访问受保护的接口"

    @staticmethod
    def ADMIN_PERMISSION_CHECK_FAILED(error: Exception) -> str:
        return f"检查管理员权限时出错: {error}"

    @staticmethod
    def INTERNAL_TOKEN_SERVICE_NAME_MISMATCH(
        expected_service_name: str, actual_service_name: Any
    ) -> str:
        return f"{Messages.SERVICE_NAME_MISMATCH}. 期望: {expected_service_name}, 获得: {actual_service_name}"

    @staticmethod
    def INTERNAL_TOKEN_VERIFICATION_SUCCESS(user_id: Any, service_name: Any) -> str:
        return f"内部令牌验证成功 - 用户ID: {user_id}, 服务: {service_name}"

    @staticmethod
    def INTERNAL_TOKEN_VERIFICATION_FAILED(error: Exception) -> str:
        return f"令牌验证失败: {error}"

    @staticmethod
    def BUSINESS_EXCEPTION_LOG(
        request_url: Any, error_code: str, error: Exception
    ) -> str:
        return f"请求路径: {request_url}，业务错误: [{error_code}] {error}"

    @staticmethod
    def GLOBAL_EXCEPTION_LOG(request_url: Any, error: Exception) -> str:
        return f"请求路径: {request_url}，错误信息: {error}"

    @staticmethod
    def REQUEST_VALIDATION_EXCEPTION_LOG(request_url: Any, message: str) -> str:
        return f"请求路径: {request_url}，校验错误: {message}"

    @staticmethod
    def API_LOG_RESPONSE_TIME(method: str, path: str, duration_ms: int) -> str:
        return f"{method} {path} 使用了{duration_ms}ms"

    @staticmethod
    def API_LOG_RESPONSE_TIME_WITH_ERROR(
        method: str, path: str, duration_ms: int, error: Exception
    ) -> str:
        return f"{method} {path} 使用了{duration_ms}ms (异常)，异常信息: {error}"

    @staticmethod
    def API_LOG_REQUEST_PROCESS_FAILED(error: Exception) -> str:
        return f"请求处理异常: {error}"

    @staticmethod
    def API_LOG_REQUEST_ERROR_ID(error: Exception) -> str:
        return f"REQUEST_ERROR: {str(error)[:200]}"

    @staticmethod
    def API_LOG_PARAM_PARSE_FAILED(error: Exception) -> str:
        return f"参数解析失败: {error}"

    @staticmethod
    def API_LOG_REQUEST_BODY_EXTRACTION_FAILED(error: Exception) -> str:
        return f"提取请求体信息时出错: {error}"

    @staticmethod
    def API_LOG_QUEUE_SEND_FAILED(error: Exception) -> str:
        return f"发送 API 日志到队列时出错: {error}"

    @staticmethod
    def USER_ROLE_MAPPER_UNINITIALIZED(user_id: int) -> str:
        return f"用户Mapper未初始化，无法获取用户 {user_id} 的角色，使用默认角色 'user'"

    @staticmethod
    def USER_ROLE_LOADED(user_id: int, role: str) -> str:
        return f"用户 {user_id} 的角色: {role}"

    @staticmethod
    def USER_ROLE_LOAD_FAILED(user_id: int, error: Exception) -> str:
        return f"获取用户 {user_id} 的角色失败: {error}，使用默认角色 'user'"

    @staticmethod
    def PERSONAL_INFO_KEYWORD_DETECTED(keyword: str) -> str:
        return f"[权限] 检测到个人信息查询关键字: '{keyword}'"

    @staticmethod
    def TOOL_ACCESS_LOGIN_REQUIRED(tool_name: str) -> str:
        return f"权限拒绝：请先登录才能访问{tool_name}功能。您当前可以使用文章搜索和闲聊功能。"

    @staticmethod
    def PERSONAL_TOOL_ACCESS_GRANTED(user_id: int, tool_type: str) -> str:
        return f"用户 {user_id} 查询个人信息，允许访问 {tool_type} 工具"

    @staticmethod
    def ADMIN_TOOL_ACCESS_GRANTED(user_id: int, role: str, tool_type: str) -> str:
        return f"用户 {user_id} (角色: {role}) 有权访问 {tool_type} 工具"

    @staticmethod
    def TOOL_ACCESS_DENIED_REASON(tool_name: str) -> str:
        return f"权限拒绝：您的账户权限不足，无法访问{tool_name}功能。仅管理员账户可以使用此功能。如需查询个人信息（如'我的点赞文章'），请在问题中包含相关关键词。"

    @staticmethod
    def TOOL_ACCESS_DENIED_LOG(
        user_id: int, role: Optional[str], tool_type: str, question: str
    ) -> str:
        return (
            f"用户 {user_id} (角色: {role}) 尝试访问 {tool_type} 工具被拒绝：{question}"
        )

    @staticmethod
    def CHAT_SERVICE_PROCESSING(
        service_name: str, user_id: str, streaming: bool
    ) -> str:
        suffix = "流式服务" if streaming else "服务"
        return f"使用{service_name}{suffix}处理用户 {user_id} 的请求"

    @staticmethod
    def AI_HISTORY_SAVED(user_id: str, ai_type: str, streaming: bool) -> str:
        prefix = "流式" if streaming else ""
        return f"{prefix}AI历史记录已保存: user_id={user_id}, ai_type={ai_type}"

    @staticmethod
    def STREAM_CHUNK_RECEIVED(chunk_type: str, content_length: int) -> str:
        return f"流式块类型: {chunk_type}, 块内容长度: {content_length}"

    @staticmethod
    def SSE_PACKET_SIZE(size: int) -> str:
        return f"SSE 数据包大小: {size} 字节"

    @staticmethod
    def API_LOG_REQUEST_MESSAGE(
        user_id: str, username: str, method: str, path: str, message: str
    ) -> str:
        return f"用户{user_id}:{username} {method} {path}: {message}"

    @staticmethod
    def API_LOG_QUERY_PARAMS(params: str) -> str:
        return f"  查询参数: {params}"

    @staticmethod
    def API_LOG_PATH_PARAMS(params: str) -> str:
        return f"  路径参数: {params}"

    @staticmethod
    def API_LOG_PARAM_LINE(key: str, value: str) -> str:
        return f"    {key}: {value}"

    @staticmethod
    def UPLOAD_FILE_DESCRIPTION(filename: str) -> str:
        return f"UploadFile(filename='{filename}')"

    @staticmethod
    def LLM_TOOL_LOADED(tool_name: str, count: int) -> str:
        return f"已加载 {tool_name} 工具: {count} 个"

    @staticmethod
    def LLM_TOOL_LOAD_FAILED(tool_name: str, error: Exception) -> str:
        return f"加载 {tool_name} 工具失败: {error}"

    @staticmethod
    def LLM_TOOLS_LOADED_TOTAL(count: int) -> str:
        return f"总共加载了 {count} 个工具"

    @staticmethod
    def LLM_CHAT_HISTORY_LOAD_FAILED(error: Exception) -> str:
        return f"加载聊天历史失败: {error}"

    @staticmethod
    def LLM_INVALID_USER_ID(user_id: Any) -> str:
        return f"用户ID格式不合法，已忽略: {user_id}"

    @staticmethod
    def LLM_AGENT_INITIALIZATION_PARTIAL_FAILED(error: Exception) -> str:
        return f"工具初始化部分失败: {error}, 降级为基础对话模式"

    @staticmethod
    def INTERNAL_TOKEN_GENERATION_FAILED(error: Exception) -> str:
        return f"生成内部令牌失败: {error}"

    @staticmethod
    def REMOTE_SERVICE_RETRY(attempt: int, error: BaseException | None) -> str:
        return f"调用远程服务失败，准备第 {attempt} 次重试: {error}"

    @staticmethod
    def REMOTE_SERVICE_CIRCUIT_OPEN(service_name: str) -> str:
        return f"调用 {service_name} 已触发熔断，直接降级返回"

    @staticmethod
    def REMOTE_SERVICE_DEGRADED(service_name: str) -> str:
        return f"调用远程服务 {service_name} 已降级，请稍后再试"

    @staticmethod
    def REMOTE_SERVICE_NON_SUCCESS(
        service_name: str, status_code: int, url: Any
    ) -> str:
        return f"调用 {service_name} 返回非 2xx 状态码: {status_code}, url={url}"

    @staticmethod
    def REMOTE_SERVICE_NETWORK_ERROR(service_name: str, error: Exception) -> str:
        return f"调用 {service_name} 网络异常: {error}"

    @staticmethod
    def REMOTE_SERVICE_RESPONSE_PARSE_ERROR(service_name: str, error: Exception) -> str:
        return f"调用 {service_name} 响应解析失败: {error}"

    @staticmethod
    def REMOTE_SERVICE_CALL_ERROR(service_name: str, error: Exception) -> str:
        return f"调用 {service_name} 失败: {error}"

    @staticmethod
    def REMOTE_SERVICE_UNAVAILABLE(service_name: str) -> str:
        return f"调用远程服务 {service_name} 失败，请稍后重试"

    @staticmethod
    def REMOTE_SERVICE_REQUEST(
        service_name: str, method: str, url: str, attempt: int
    ) -> str:
        return f"正在调用 {service_name} 的接口：{method} {url}（第 {attempt} 次尝试）"

    @staticmethod
    def REMOTE_SERVICE_BUSINESS_ERROR(
        service_name: str, code: Any, message: str
    ) -> str:
        return f"服务 {service_name} 返回业务错误: code={code}, msg={message}"

    @staticmethod
    def REMOTE_SERVICE_CALL_FAILED(service_name: str, message: str) -> str:
        return f"调用远程服务 {service_name} 失败: {message}"

    @staticmethod
    def NACOS_LOCAL_IP_RESOLVED(ip: str) -> str:
        return f"自动解析本地 IP: {ip}"

    @staticmethod
    def NACOS_LOCAL_IP_RESOLVE_FAILED(error: Exception) -> str:
        return f"自动解析 IP 失败: {error}，使用主机名"

    @staticmethod
    def NACOS_REGISTERED(service_name: str, ip: str, port: int, group_name: str) -> str:
        return f"Nacos 注册成功: service={service_name}, address={ip}:{port}, group={group_name}"

    @staticmethod
    def NACOS_REGISTER_RETRY(attempt: int, retries: int, error: Exception) -> str:
        return f"Nacos 注册失败，第 {attempt}/{retries} 次重试: {error}"

    @staticmethod
    def NACOS_REGISTER_FAILED(retries: int, server_addresses: str) -> str:
        return f"Nacos 注册失败，已重试 {retries} 次，server={server_addresses}"

    @staticmethod
    def NACOS_HEARTBEAT_ERROR(error: Exception) -> str:
        return f"Nacos 心跳错误: {error}"

    @staticmethod
    def CONFIG_FILE_NOT_FOUND(searched_paths: str) -> str:
        return f"未找到 application.yaml，请确认配置文件存在。已搜索路径:\n{searched_paths}"

    @staticmethod
    def CLICKHOUSE_POOL_REUSED(remaining: int) -> str:
        return f"[ClickHouse连接池] 从池中获取复用连接，池内剩余: {remaining}个"

    @staticmethod
    def CLICKHOUSE_POOL_EXHAUSTED(active: int, maximum: int) -> str:
        return f"[ClickHouse连接池] 连接池已耗尽，等待可用连接 (活跃连接: {active}/{maximum})"

    @staticmethod
    def CLICKHOUSE_POOL_REUSED_AFTER_WAIT(remaining: int) -> str:
        return f"[ClickHouse连接池] 等待后获取复用连接，池内剩余: {remaining}个"

    @staticmethod
    def CLICKHOUSE_CONNECTION_CREATING(index: int) -> str:
        return f"[ClickHouse连接池] 创建新连接 (第{index}个)"

    @staticmethod
    def CLICKHOUSE_CONNECTION_CONFIG(
        host: str, port: int, database: str, user: str
    ) -> str:
        return f"[ClickHouse连接池] 连接配置 - Host: {host}, Port: {port}, DB: {database}, User: {user}"

    @staticmethod
    def CLICKHOUSE_CONNECTION_CREATED(duration: float) -> str:
        return f"[ClickHouse连接池] 连接建立耗时 {duration:.3f}s"

    @staticmethod
    def CLICKHOUSE_CONNECTION_CREATE_FAILED(error: Exception) -> str:
        return f"[ClickHouse连接池] 创建连接失败: {error}"

    @staticmethod
    def CLICKHOUSE_VALUE_CONVERSION_FAILED(col: str, val: Any, error: Exception) -> str:
        return f"值转换失败 {col}={val}: {error}"

    @staticmethod
    def CLICKHOUSE_ROW_CONVERSION_FAILED(error: Exception) -> str:
        return f"行数据转换失败: {error}"

    @staticmethod
    def CLICKHOUSE_QUERY_TIMING(
        pool_time: float, query_time: float, total_time: float
    ) -> str:
        return f"获取连接耗时 {pool_time:.3f}s, 查询耗时 {query_time:.3f}s, 总耗时 {total_time:.3f}s"

    @staticmethod
    def CLICKHOUSE_ATTR_ERROR(error: Exception) -> str:
        return f"ClickHouse 查询失败，属性错误: {error}"

    @staticmethod
    def CLICKHOUSE_QUERY_ROW_CONVERSION_FAILED(error: Exception) -> str:
        return f"行转换失败: {error}，跳过此行"

    @staticmethod
    def CLICKHOUSE_CATEGORY_QUERY_RESULT(
        query_time: float, total_time: float, result_count: int
    ) -> str:
        return f"查询耗时 {query_time:.3f}s, 总耗时 {total_time:.3f}s, 获取 {result_count} 个分类"

    @staticmethod
    def CLICKHOUSE_MONTHLY_QUERY_RESULT(
        query_time: float, total_time: float, result_count: int
    ) -> str:
        return f"查询耗时 {query_time:.3f}s, 总耗时 {total_time:.3f}s, 获取过去24个月中 {result_count} 个有数据的月份"

    @staticmethod
    def CLICKHOUSE_DEGRADE_TO_DB(error_type: str, error: Exception) -> str:
        return f"ClickHouse 查询失败，降级为 DB: {error_type}: {error}"

    @staticmethod
    def CLICKHOUSE_DETAIL_ERROR(traceback_text: str) -> str:
        return f"详细错误: {traceback_text}"

    @staticmethod
    def CLICKHOUSE_DETAIL_EXCEPTION(traceback_text: str) -> str:
        return f"详细异常: {traceback_text}"

    @staticmethod
    def CLICKHOUSE_CONNECTION_RETURNED(count: int) -> str:
        return f"[ClickHouse连接池] 连接已归还到池，池内现有: {count}个"

    @staticmethod
    def DATABASE_TABLE_CREATION_FAILED(error: Exception) -> str:
        return f"数据库表创建失败: {error}"

    @staticmethod
    def NEO4J_CONFIG_INITIALIZED(uri: str) -> str:
        return f"Neo4j 连接参数初始化成功: {uri}"

    @staticmethod
    def NEO4J_CONFIG_INITIALIZATION_FAILED(error: Exception) -> str:
        return f"Neo4j 连接参数初始化失败: {error}"

    @staticmethod
    def NEO4J_DRIVER_INITIALIZED(uri: str) -> str:
        return f"Neo4j 驱动初始化成功: {uri}"

    @staticmethod
    def CYPHER_QUERY_FAILED(error: Exception, cypher: str, params: Any) -> str:
        return f"Cypher 查询失败: {error}\nCypher: {cypher}\nParams: {params}"

    @staticmethod
    def CYPHER_WRITE_FAILED(error: Exception, cypher: str, params: Any) -> str:
        return f"Cypher 写操作失败: {error}\nCypher: {cypher}\nParams: {params}"

    @staticmethod
    def POSTGRES_CONNECTION_STRING_CREATED(host: str, port: Any, database: str) -> str:
        return f"PostgreSQL 连接字符串构建成功: {host}:{port}/{database}"

    @staticmethod
    def POSTGRES_CONNECTION_STRING_CREATE_FAILED(error: Exception) -> str:
        return f"PostgreSQL 连接字符串构建失败: {error}"

    @staticmethod
    def RABBITMQ_CONNECTION_FAILED(error: Exception) -> str:
        return f"RabbitMQ 连接失败: {error}"

    @staticmethod
    def RABBITMQ_RECONNECT_CHANNEL_FAILED(error: Exception) -> str:
        return f"RabbitMQ 重连后恢复 channel 失败: {error}"

    @staticmethod
    def RABBITMQ_MESSAGE_SENT(queue_name: str, body: str) -> str:
        return f"消息已发送到队列 [{queue_name}]: {body[:100]}..."

    @staticmethod
    def RABBITMQ_MESSAGE_SEND_FAILED(queue_name: str, error: Exception) -> str:
        return f"发送消息到队列 [{queue_name}] 失败: {error}"

    @staticmethod
    def RABBITMQ_CONNECTION_CLOSE_FAILED(error: Exception) -> str:
        return f"关闭 RabbitMQ 连接失败: {error}"

    @staticmethod
    def RABBITMQ_CLIENT_INITIALIZATION_FAILED(error: Exception) -> str:
        return f"初始化 RabbitMQ 客户端失败: {error}"

    @staticmethod
    def RABBITMQ_SEND_FAILED(error: Exception) -> str:
        return f"发送消息失败: {error}"

    @staticmethod
    def REFERENCE_EXTRACTOR_ERROR(action: str, error: Exception) -> str:
        return f"{action}: {error}"

    @staticmethod
    def REFERENCE_CONTENT_STARTED(content_type: str, value: str) -> str:
        return f"开始{content_type}: {value}"

    @staticmethod
    def REFERENCE_CONTENT_COMPLETED(content_type: str, length: int) -> str:
        return f"{content_type}完成，长度: {length}"

    @staticmethod
    def REFERENCE_TYPE_UNSUPPORTED(
        reference_type: str, synchronous: bool = False
    ) -> str:
        prefix = "同步模式" if synchronous else ""
        return f"{prefix}不支持的内容类型: {reference_type}"

    @staticmethod
    def REFERENCE_SUMMARIZED(source_length: int, summary_length: int) -> str:
        return f"AI总结完成，原长度: {source_length}, 总结长度: {summary_length}"

    @staticmethod
    def INTENT_STRUCTURED_OUTPUT_UNAVAILABLE(error: Exception) -> str:
        return f"with_structured_output 不可用，降级为文本匹配模式: {error}"

    @staticmethod
    def INTENT_RECOGNITION_FAILED(error: Exception) -> str:
        return f"意图识别失败: {error}, 默认使用 article_search"

    @staticmethod
    def INTENT_STRUCTURED_RESULT(question: str, intent: str, confidence: float) -> str:
        return (
            f"意图识别结果(结构化): {question} -> {intent} (置信度: {confidence:.2f})"
        )

    @staticmethod
    def INTENT_STRUCTURED_FALLBACK(error: Exception) -> str:
        return f"结构化意图识别失败，降级为文本匹配: {error}"

    @staticmethod
    def INTENT_TEXT_RESULT(question: str, intent: str) -> str:
        return f"意图识别结果(文本匹配): {question} -> {intent}"

    @staticmethod
    def INTENT_WRITE_SQL_BLOCKED(question: str) -> str:
        return f"拦截疑似写操作SQL请求: {question}"

    @staticmethod
    def INTENT_WRITE_CHECK_FAILED(error: Exception) -> str:
        return f"写操作意图检测失败，继续执行权限校验: {error}"

    @staticmethod
    def LANGSMITH_CLIENT_INITIALIZED(project: str, endpoint: str) -> str:
        return f"LangSmith 客户端初始化成功，项目: {project}，端点: {endpoint}"

    @staticmethod
    def LANGSMITH_CLIENT_INITIALIZATION_FAILED(error: Exception) -> str:
        return f"LangSmith 客户端初始化失败: {error}"

    @staticmethod
    def LANGSMITH_CLIENT_CLOSE_FAILED(error: Exception) -> str:
        return f"LangSmith 客户端关闭异常: {error}"

    @staticmethod
    def LANGSMITH_RUN_CREATE_FAILED(error: Exception) -> str:
        return f"创建 LangSmith Run 失败: {error}"

    @staticmethod
    def LANGSMITH_RUN_END_FAILED(error: Exception) -> str:
        return f"结束 LangSmith Run 失败: {error}"

    @staticmethod
    def SANITIZED_TEXT_TRUNCATED(length: int) -> str:
        return f"...[截断,原长{length}]"

    @staticmethod
    def SANITIZED_TOOL_INPUT_HIDDEN(type_name: str) -> str:
        return f"[{type_name} 类型输入已隐藏]"

    @staticmethod
    def SANITIZED_OUTPUT_TRUNCATED(length: int, preview: str) -> str:
        return f"[输出已截断, 原长 {length}] {preview}..."

    @staticmethod
    def SANITIZED_TOOL_OUTPUT_LENGTH(length: int) -> str:
        return f"[工具输出, 长度: {length}]"

    @staticmethod
    def SANITIZED_MAX_DEPTH(depth: int) -> str:
        return f"超过最大深度 {depth}"

    @staticmethod
    def SANITIZED_LIST_MAX_DEPTH(depth: int) -> str:
        return f"[超过最大深度 {depth}]"

    @staticmethod
    def SANITIZED_LIST_TRUNCATED(count: int) -> str:
        return f"...[截断, 共 {count} 项]"

    @staticmethod
    def MONGODB_LOG_COLLECTION_GET_FAILED(error: Exception) -> str:
        return f"获取日志集合失败: {error}"

    @staticmethod
    def MONGODB_COLLECTION_INFO_GET_FAILED(
        collection_name: str, error: Exception
    ) -> str:
        return f"无法获取 {collection_name} 的信息: {error}"

    @staticmethod
    def MONGODB_COLLECTION_LIST_FAILED(error: Exception) -> str:
        return f"获取 collection 列表失败: {error}"

    @staticmethod
    def MONGODB_QUERY_RESULT(collection_name: str, filter_obj: Any, count: int) -> str:
        return f"查询 {collection_name}: 条件={filter_obj}, 返回 {count} 条记录"

    @staticmethod
    def MONGODB_QUERY_FAILED(error: Exception) -> str:
        return f"MongoDB 查询失败: {error}"

    @staticmethod
    def CACHE_L1_HIT(age: float) -> str:
        return f"[L1缓存] 命中，缓存年龄: {age:.1f}s"

    @staticmethod
    def CACHE_L2_READ_FAILED(error: Exception) -> str:
        return f"[L2缓存] Redis 读取失败: {error}"

    @staticmethod
    def CACHE_L2_UPDATED(ttl: int) -> str:
        return f"[L2缓存] 已更新 Redis，TTL={ttl}s (1天)"

    @staticmethod
    def CACHE_L2_WRITE_FAILED(error: Exception) -> str:
        return f"[L2缓存] Redis 写入失败: {error}"

    @staticmethod
    def CACHE_L2_CLEAR_FAILED(error: Exception) -> str:
        return f"[L2缓存] Redis 清除失败: {error}"

    @staticmethod
    def CACHE_VERSION_GET_FAILED(error: Exception) -> str:
        return f"获取版本号失败: {type(error).__name__}: {error}"

    @staticmethod
    def CACHE_VERSION_REDIS_READ_FAILED(error: Exception) -> str:
        return f"[缓存] Redis 读取版本号失败: {error}"

    @staticmethod
    def CACHE_VERSION_INITIALIZED(version: str) -> str:
        return f"[缓存] 首次初始化，当前版本: {version}"

    @staticmethod
    def CACHE_VERSION_CHANGED(old_version: str, new_version: str) -> str:
        return f"[缓存] 表版本已变化 (旧: {old_version} → 新: {new_version})"

    @staticmethod
    def CACHE_VERSION_CHECK_FAILED(error: Exception) -> str:
        return f"版本检测异常: {error}"

    @staticmethod
    def CACHE_VERSION_UPDATED(version: str) -> str:
        return f"[缓存] 版本号已更新: {version}"

    @staticmethod
    def CACHE_VERSION_SET_FAILED(error: Exception) -> str:
        return f"设置缓存版本号失败: {error}"

    @staticmethod
    def CACHE_VERSION_CLEAR_FAILED(error: Exception) -> str:
        return f"[L2缓存] Redis 清除版本号失败: {error}"

    @staticmethod
    def NEO4J_QUERY_TOOL_INITIALIZATION_FAILED(error: Exception) -> str:
        return f"Neo4j 查询工具初始化失败: {error}"

    @staticmethod
    def NEO4J_QUERY_TYPE_UNSUPPORTED(available: str) -> str:
        return f"不支持的查询类型，可选: {available}"

    @staticmethod
    def NEO4J_QUERY_RESULT_HEADER(query_name: str, count: int) -> str:
        return f"查询 {query_name} 返回 {count} 条结果:"

    @staticmethod
    def NEO4J_QUERY_FIELD(key: str, value: str) -> str:
        return f"{key}: {value}"

    @staticmethod
    def NEO4J_QUERY_RESULT_ROW(index: int, fields: str) -> str:
        return f"{index}. {fields}"

    @staticmethod
    def USER_MONTHLY_TREND(user_id: int, trend_name: str, total: int, days: int) -> str:
        return f"用户 {user_id} 本月{trend_name}趋势: 总数={total}, 天数={days}"

    @staticmethod
    def ARTICLE_VIEW_DISTRIBUTION_QUERY_STARTED(user_id: int) -> str:
        return f"开始查询用户 {user_id} 的浏览分布"

    @staticmethod
    def ARTICLE_VIEW_DISTRIBUTION_EMPTY(user_id: int) -> str:
        return f"用户 {user_id} 无浏览记录"

    @staticmethod
    def ARTICLE_VIEW_DISTRIBUTION_RESULT(
        user_id: int, total: int, articles: int
    ) -> str:
        return f"用户 {user_id} 的文章浏览分布: 总浏览数={total}, 文章数={articles}"

    @staticmethod
    def ARTICLE_VIEW_DISTRIBUTION_FAILED(error: Exception) -> str:
        return f"获取文章浏览分布失败: {error}"

    @staticmethod
    def USER_NEW_FOLLOWER_COUNT_FAILED(error: Exception) -> str:
        return f"获取新增粉丝数统计失败: {error}"

    @staticmethod
    def USER_AUTHOR_FOLLOW_STATS_FAILED(error: Exception) -> str:
        return f"获取关注作者统计失败: {error}"

    @staticmethod
    def USER_COMMENT_TREND_FAILED(error: Exception) -> str:
        return f"获取评论趋势失败: {error}"

    @staticmethod
    def USER_LIKE_TREND_FAILED(error: Exception) -> str:
        return f"获取点赞趋势失败: {error}"

    @staticmethod
    def USER_COLLECT_TREND_FAILED(error: Exception) -> str:
        return f"获取收藏趋势失败: {error}"

    @staticmethod
    def RAG_TOOL_PROMPT_INJECTION_DETECTED() -> str:
        return "检测到疑似 Prompt 注入内容，已过滤"

    @staticmethod
    def RAG_TOOL_FILTERED_PLACEHOLDER() -> str:
        return "[已过滤]"

    @staticmethod
    def EMBEDDING_CACHE_ENABLED() -> str:
        return "Embedding 缓存已启用"

    @staticmethod
    def EMBEDDING_CACHE_ENABLE_FAILED(error: Exception) -> str:
        return f"Embedding 缓存启用失败: {error}"

    @staticmethod
    def EMBEDDING_MODEL_INITIALIZED(embedding_model: str) -> str:
        return f"Embedding嵌入模型初始化成功: {embedding_model}"

    @staticmethod
    def EMBEDDING_INIT_FAILED(error: Exception) -> str:
        return f"Embedding初始化失败，请检查 DashScope API Key 是否有效：{error}"

    @staticmethod
    def HYDE_LLM_INITIALIZED() -> str:
        return "HyDE LLM 初始化成功（假设性文档生成增强已启用）"

    @staticmethod
    def HYDE_LLM_INIT_FAILED(error: Exception) -> str:
        return f"HyDE LLM 初始化失败，将使用纯 query 检索: {error}"

    @staticmethod
    def RAG_BATCH_ADDED_ARTICLES(article_ids_count: int, doc_count: int) -> str:
        return f"成功添加 {article_ids_count} 篇文章，共 {doc_count} 个文本块到向量存储"

    @staticmethod
    def RAG_BATCH_ADD_FAILED(error: Exception) -> str:
        return f"添加文章到向量存储失败: {str(error)}"

    @staticmethod
    def HYDE_GENERATION_SUCCESS(query_len: int, hyde_len: int) -> str:
        return (
            f"HyDE 假设性文档生成成功（原始查询: {query_len} 字 → HyDE: {hyde_len} 字）"
        )

    @staticmethod
    def HYDE_GENERATION_FAILED(error: Exception) -> str:
        return f"HyDE 生成失败，降级为原查询: {error}"

    @staticmethod
    def RAG_SEARCH_SUCCESS(
        dedup_count: int, before_dedup: int, before_filter: int
    ) -> str:
        return f"RAG搜索成功，返回 {dedup_count} 个结果（去重前: {before_dedup}，过滤前: {before_filter}）"

    @staticmethod
    def RAG_SEARCH_FAILED(error: Exception) -> str:
        return f"RAG搜索失败: {str(error)}"

    @staticmethod
    def RAG_CONTEXT_FETCH_SUCCESS(dedup_count: int, before_dedup: int) -> str:
        return (
            f"获取文章上下文成功，返回 {dedup_count} 个文档（去重前: {before_dedup}）"
        )

    @staticmethod
    def RAG_CONTEXT_FETCH_FAILED(error: Exception) -> str:
        return f"获取文章上下文失败: {error}"

    @staticmethod
    def SQL_TOOL_USER_ID_SET(user_id: int) -> str:
        return f"设置SQL工具用户ID: {user_id}"

    @staticmethod
    def SQL_TOOL_TABLE_NOT_FOUND(table_name: str) -> str:
        return f"表 '{table_name}' 不存在"

    @staticmethod
    def SQL_TOOL_GET_SCHEMA_FAILED(error: Exception) -> str:
        return f"获取表结构失败: {str(error)}"

    @staticmethod
    def SQL_TOOL_ADD_USER_FILTER(current_user_id: int) -> str:
        return f"[SQL工具] 为用户 {current_user_id} 的查询添加用户ID过滤"

    @staticmethod
    def SQL_TOOL_QUERY_SUCCESS(row_count: int) -> str:
        return f"SQL查询成功，返回 {row_count} 行"

    @staticmethod
    def SQL_TOOL_QUERY_FAILED(error: Exception) -> str:
        return f"SQL查询失败: {str(error)}"

    @staticmethod
    def CATEGORY_REFERENCE_QUERY_STARTED(sub_category_id: int) -> str:
        return f"获取子分类 {sub_category_id} 的权威参考文本"

    @staticmethod
    def CATEGORY_REFERENCE_FOUND(reference_type: str) -> str:
        return f"成功获取参考文本: type={reference_type}"

    @staticmethod
    def CATEGORY_REFERENCE_NOT_FOUND(sub_category_id: int) -> str:
        return f"子分类 {sub_category_id} 无权威参考文本"

    @staticmethod
    def ANALYZE_CACHE_UPDATE_FAILED(cache_name: str, error: Exception) -> str:
        return f"{cache_name}缓存更新失败: {error}"

    @staticmethod
    def ANALYZE_CACHE_TASK_FAILED(error: Exception) -> str:
        return f"update_analyze_caches 发生异常: {error}"

    @staticmethod
    def DATABASE_CONNECTION_CLOSE_FAILED(error: Exception) -> str:
        return f"关闭数据库连接失败: {error}"

    @staticmethod
    def NEO4J_SYNC_NO_DATA(label: str) -> str:
        return f"[知识图谱] 无 {label} 需要同步"

    @staticmethod
    def NEO4J_SYNC_PROGRESS(label: str, total: int, count: int) -> str:
        return f"[知识图谱] 已同步 {label}: {total}/{count}"

    @staticmethod
    def NEO4J_SYNC_CLEANUP(label: str, deleted_count: int) -> str:
        return f"[知识图谱] 已清理 {label}: {deleted_count}"

    @staticmethod
    def NEO4J_SYNC_TIME_SAVED(sync_time: str) -> str:
        return f"[知识图谱] 已保存同步时间戳到 Redis: {sync_time}"

    @staticmethod
    def NEO4J_SYNC_TIME_SAVE_FAILED(error: Exception) -> str:
        return f"[知识图谱] 保存同步时间戳到 Redis 失败: {error}"

    @staticmethod
    def NEO4J_SYNC_TIME_READ_FAILED(error: Exception) -> str:
        return f"从 Redis 读取 Neo4j 同步时间戳失败: {error}"

    @staticmethod
    def NEO4J_MYSQL_SYNC_FAILED(error: Exception) -> str:
        return f"[知识图谱任务] MySQL 到 Neo4j 同步失败: {error}"

    # ===== 生成模块 =====
    @staticmethod
    def ARTICLE_AI_COMMENT_EXISTS_DELETING(article_id: int) -> str:
        return f"文章ID：{article_id} 已存在AI评论，删除对应AI评论"

    @staticmethod
    def CONCURRENT_LLM_AI_COMMENT_START(article_id: int) -> str:
        return f"开始并发调用3个大模型生成AI评论，文章ID：{article_id}"

    @staticmethod
    def LLM_CALL_COMPLETED(service_name: str, duration: float) -> str:
        return f"{service_name}调用完成，耗时: {duration:.2f}秒"

    @staticmethod
    def LLM_CALL_FAILED_TIMED(
        service_name: str, duration: float, error: Exception
    ) -> str:
        return f"{service_name}调用失败，耗时: {duration:.2f}秒，错误: {error}"

    @staticmethod
    def CONCURRENT_LLM_ALL_COMPLETED(duration: float, article_id: int) -> str:
        return (
            f"3个大模型并发调用全部完成，总耗时: {duration:.2f}秒，文章ID：{article_id}"
        )

    @staticmethod
    def LLM_FINAL_FAILED(service_name: str, response: Any) -> str:
        return f"{service_name}大模型最终失败: {response}"

    @staticmethod
    def AI_COMMENT_GENERATED_AND_SAVED(article_id: int) -> str:
        return f"AI评论生成并保存完成，文章ID：{article_id}"

    @staticmethod
    def ARTICLE_NOT_FOUND_WITH_ID(article_id: int) -> str:
        return f"文章不存在: {article_id}"

    @staticmethod
    def REFERENCE_BASED_AI_COMMENT_START(article_id: int) -> str:
        return f"开始基于参考文本生成AI评论，文章ID：{article_id}"

    @staticmethod
    def REFERENCE_TEXT_TYPE_FOUND(ref_type: str) -> str:
        return f"找到权威参考文本，类型: {ref_type}"

    @staticmethod
    def REFERENCE_TEXT_DETAIL(category_ref: Any) -> str:
        return f"参考文本详情: {category_ref}"

    @staticmethod
    def REFERENCE_PDF_EXTRACTION_START(ref_value: str) -> str:
        return f"开始提取 PDF 权威文本: {ref_value}"

    @staticmethod
    def REFERENCE_LINK_EXTRACTION_START(ref_value: str) -> str:
        return f"开始提取链接权威文本: {ref_value}"

    @staticmethod
    def LLM_SUMMARIZE_FAILED(service_name: str, error: Exception) -> str:
        return f"{service_name}总结失败: {error}"

    @staticmethod
    def LLM_SUMMARY_RESULT_HEADER(service_name: str) -> str:
        return f"【{service_name}总结】"

    @staticmethod
    def LLM_SUMMARY_RESULT_ENTRY(service_name: str, content: str) -> str:
        return f"【{service_name}总结】\n{content}"

    @staticmethod
    def REFERENCE_TEXT_EXTRACTED_AND_SUMMARIZED(length: int) -> str:
        return f"权威参考文本提取并总结完成，总结内容长度: {length} 字"

    @staticmethod
    def REFERENCE_TEXT_EXTRACTION_FAILED_TYPE(ref_type: str) -> str:
        return f"无法提取或总结参考文本内容，类型: {ref_type}"

    @staticmethod
    def REFERENCE_TEXT_FALLBACK_CONTENT(ref_type: str, ref_value: str) -> str:
        return f"参考文本类型: {ref_type}\n参考文本链接: {ref_value}"

    @staticmethod
    def SUB_CATEGORY_NO_REFERENCE(sub_category_id: int) -> str:
        return f"子分类 {sub_category_id} 无权威参考文本"

    @staticmethod
    def ARTICLE_NO_SUB_CATEGORY(article_id: int) -> str:
        return f"文章 {article_id} 无子分类信息"

    @staticmethod
    def CONCURRENT_LLM_REFERENCE_AI_COMMENT_START(article_id: int) -> str:
        return f"开始并发调用3个大模型生成AI评论（基于参考文本），文章ID：{article_id}"

    @staticmethod
    def LLM_REFERENCE_CALL_COMPLETED(service_name: str, duration: float) -> str:
        return f"{service_name}参考文本调用完成，耗时: {duration:.2f}秒"

    @staticmethod
    def LLM_REFERENCE_CALL_FAILED_TIMED(
        service_name: str, duration: float, error: Exception
    ) -> str:
        return f"{service_name}参考文本调用失败，耗时: {duration:.2f}秒，错误: {error}"

    @staticmethod
    def CONCURRENT_LLM_REFERENCE_ALL_COMPLETED(duration: float, article_id: int) -> str:
        return f"3个大模型参考文本并发调用全部完成，总耗时: {duration:.2f}秒，文章ID：{article_id}"

    @staticmethod
    def LLM_REFERENCE_FINAL_FAILED(service_name: str, response: Any) -> str:
        return f"{service_name}参考文本最终失败: {response}"

    @staticmethod
    def REFERENCE_AI_COMMENT_GENERATED_AND_SAVED(article_id: int) -> str:
        return f"基于参考文本的AI评论生成并保存完成，文章ID：{article_id}"

    @staticmethod
    def AUTHORITY_ARTICLE_GENERATION_START(ref_type: str, ref_value: str) -> str:
        return f"开始生成权威文章，类型: {ref_type}，值: {ref_value}"

    @staticmethod
    def UNSUPPORTED_REFERENCE_TYPE(ref_type: str) -> str:
        return f"不支持的参考文本类型: {ref_type}"

    @staticmethod
    def RAW_CONTENT_EXTRACTION_COMPLETED(length: int) -> str:
        return f"原始内容提取完成，长度: {length} 字符"

    @staticmethod
    def LLM_SUMMARIZE_COMPLETED(service_name: str, duration: float, length: int) -> str:
        return f"{service_name}总结完成，耗时: {duration:.2f}秒，长度: {length}"

    @staticmethod
    def LLM_SUMMARIZE_FAILED_TIMED(
        service_name: str, duration: float, error: Exception
    ) -> str:
        return f"{service_name}总结失败，耗时: {duration:.2f}秒，错误: {error}"

    @staticmethod
    def ALL_CONCURRENT_SUMMARIZE_COMPLETED(duration: float) -> str:
        return f"三个大模型总结任务全部完成，总耗时: {duration:.2f}秒"

    @staticmethod
    def AUTHORITY_ARTICLE_GENERATION_EXCEPTION(error: str) -> str:
        return f"生成权威文章异常: {error}"

    @staticmethod
    def AUTHORITY_ARTICLE_GENERATION_FAILED(error: str) -> str:
        return f"生成权威文章失败: {error}"

    @staticmethod
    def CHAT_HISTORY_LINE(user_msg: str, ai_msg: str) -> str:
        return f"用户: {user_msg}\nAI: {ai_msg}"

    @staticmethod
    def THINKING_PROCESS_PREVIEW_TEXT(text: str) -> str:
        return f"思考过程内容（前2000字）: {text}"

    @staticmethod
    def THINKING_PROCESS_MIDDLE_TEXT(text: str) -> str:
        return f"思考过程内容（中间2000字）: {text}"

    @staticmethod
    def THINKING_PROCESS_END_TEXT(text: str) -> str:
        return f"思考过程内容（末尾2000字）: {text}"

    @staticmethod
    def COMPLETE_THINKING_PROCESS_TEXT(text: str) -> str:
        return f"完整思考过程: {text}"

    # ===== AI基础服务模块 =====
    @staticmethod
    def BASIC_CHAT_START(message: str) -> str:
        return f"基础对话: {message}"

    @staticmethod
    def BASIC_CHAT_REPLY_LENGTH(service_name: str, length: int) -> str:
        return f"{service_name}基础回复长度: {length} 字符"

    @staticmethod
    def BASIC_CHAT_EXCEPTION(service_name: str, error: str) -> str:
        return f"{service_name}基础对话异常: {error}"

    @staticmethod
    def REFERENCE_CHAT_START(length: int) -> str:
        return f"基于参考文本的对话（长度: {length}）"

    @staticmethod
    def REFERENCE_CHAT_REPLY_LENGTH(service_name: str, length: int) -> str:
        return f"{service_name}参考文本对话回复长度: {length} 字符"

    @staticmethod
    def REFERENCE_CHAT_EXCEPTION(service_name: str, error: str) -> str:
        return f"{service_name}参考文本对话异常: {error}"

    @staticmethod
    def SUMMARIZE_START(service_name: str, length: int) -> str:
        return f"{service_name}开始总结内容，原始长度: {length} 字符"

    @staticmethod
    def SUMMARIZE_COMPLETED(service_name: str, length: int) -> str:
        return f"{service_name}内容总结完成，总结长度: {length} 字符"

    @staticmethod
    def SUMMARIZE_EXCEPTION(service_name: str, error: str) -> str:
        return f"{service_name}内容总结异常: {error}"

    @staticmethod
    def USER_SEND_MESSAGE(user_id: Any, message: str) -> str:
        return f"用户 {user_id} 发送消息: {message}"

    @staticmethod
    def INTENT_WITH_PERMISSION(intent: str, has_permission: bool) -> str:
        return f"识别意图: {intent}, 有权限: {has_permission}"

    @staticmethod
    def USER_NO_PERMISSION_FOR_INTENT(user_id: Any, intent: str) -> str:
        return f"用户 {user_id} 无权限访问: {intent}"

    @staticmethod
    def INTENT_RECOGNIZED(intent: str) -> str:
        return f"识别意图: {intent}"

    @staticmethod
    def SQL_TOOL_SET_USER_ID(user_id: int) -> str:
        return f"为SQL工具设置用户ID: {user_id}"

    @staticmethod
    def SQL_TOOL_SET_USER_ID_FAILED(error: Exception) -> str:
        return f"设置SQL工具用户ID失败: {error}"

    @staticmethod
    def CURRENT_USER_ID_INFO(user_id: int) -> str:
        return f"当前用户ID: {user_id}\n"

    @staticmethod
    def CURRENT_QUESTION(message: str) -> str:
        return f"当前问题: {message}"

    @staticmethod
    def CHAT_REPLY_LENGTH(service_name: str, length: int) -> str:
        return f"{service_name}回复长度: {length} 字符"

    @staticmethod
    def CHAT_EXCEPTION(service_name: str, error: str) -> str:
        return f"{service_name}聊天异常: {error}"

    @staticmethod
    def USER_START_STREAMING_CHAT(user_id: Any, message: str) -> str:
        return f"用户 {user_id} 开始流式聊天: {message}"

    @staticmethod
    def STREAM_CHUNK_RECEIVED_LENGTH(length: int) -> str:
        return f"收到流式内容块，长度: {length} 字符"

    @staticmethod
    def STREAM_CHUNK_EXCEPTION(error: str) -> str:
        return f"处理流式内容块异常: {error}"

    @staticmethod
    def STREAM_BASIC_CHAT_FAILED(error: str) -> str:
        return f"基础流式对话失败: {error}"

    @staticmethod
    def PERMISSION_DENIED_STREAM_THINKING(intent: str) -> str:
        return f"检测到用户请求需要 {intent} 权限，但当前用户权限不足。"

    @staticmethod
    def STREAM_CHAT_FAILED(error: str) -> str:
        return f"流式聊天失败: {error}"

    @staticmethod
    def AGENT_EXECUTION_FAILED(error: str) -> str:
        return f"Agent执行失败: {error}"

    @staticmethod
    def THINKING_PROCESS_LENGTH(length: int) -> str:
        return f"思考过程长度: {length} 字符"

    @staticmethod
    def FINAL_STREAM_OUTPUT_FAILED(error: str) -> str:
        return f"最终流式输出失败: {error}"

    @staticmethod
    def STREAM_CHAT_EXCEPTION(error: str) -> str:
        return f"流式聊天异常: {error}"

    @staticmethod
    def AGENT_EXECUTION_PROCESS_HEADER() -> str:
        return "Agent 执行过程:\n"

    @staticmethod
    def AGENT_EXECUTION_STEP(
        step_num: int, tool_name: str, tool_input: str, observation: str
    ) -> str:
        return f"\n步骤 {step_num}:\n  工具: {tool_name}\n  输入: {tool_input}\n  结果: {observation}\n"

    @staticmethod
    def AGENT_FINAL_RESULT(result: str) -> str:
        return f"\n\n最终分析结果:\n{result}"

    @staticmethod
    def STREAM_FINAL_PROMPT(message: str, agent_result: str) -> str:
        return f"用户问题: {message}\n\n我已经获取到以下信息:\n{agent_result}\n\n请基于这些信息,用清晰、友好的方式回答用户的问题。"

    # ===== 向量同步任务模块 =====
    @staticmethod
    def VECTOR_ARTICLE_HASH_COMPUTED(title: str, hash_val: str) -> str:
        return f"计算文章 hash 完成: title='{title}...', hash={hash_val}"

    @staticmethod
    def VECTOR_ARTICLE_HASH_COMPUTE_FAILED(error: Exception) -> str:
        return f"计算文章 hash 失败: {error}"

    @staticmethod
    def VECTOR_REDIS_HASH_READ_FAILED(error: Exception) -> str:
        return f"从 Redis 读取文章 hash 失败: {error}"

    @staticmethod
    def VECTOR_REDIS_SAVE_HASH_UNAVAILABLE(article_id: int) -> str:
        return f"Redis 连接失败，无法保存文章 {article_id} 的 hash"

    @staticmethod
    def VECTOR_ARTICLE_HASH_SAVED(article_id: int, hash_val: str) -> str:
        return f"已保存文章 {article_id} 的 hash 到 Redis: {hash_val}"

    @staticmethod
    def VECTOR_ARTICLE_HASH_SAVE_FAILED(article_id: int, error: Exception) -> str:
        return f"保存文章 {article_id} 的 hash 到 Redis 失败: {error}"

    @staticmethod
    def VECTOR_REDIS_SYNC_TIME_READ_FAILED(error: Exception) -> str:
        return f"从 Redis 读取同步时间戳失败: {error}"

    @staticmethod
    def VECTOR_SYNC_TIME_SAVED(sync_time: str) -> str:
        return f"已保存同步时间戳到 Redis: {sync_time}"

    @staticmethod
    def VECTOR_SYNC_TIME_SAVE_FAILED(error: Exception) -> str:
        return f"保存同步时间戳到 Redis 失败: {error}"

    @staticmethod
    def VECTOR_ARTICLE_HASH_MISSING(article_id: int) -> str:
        return f"无法计算文章 {article_id} 的 hash"

    @staticmethod
    def VECTOR_ARTICLE_HASH_COMPARE(
        article_id: int, cached_hash: Optional[str], current_hash: str
    ) -> str:
        return f"文章 {article_id}: 缓存hash={cached_hash}, 当前hash={current_hash}"

    @staticmethod
    def VECTOR_ARTICLE_NEW_FOUND(article_id: int) -> str:
        return f"文章 {article_id} 在缓存中不存在，视为新增，将同步"

    @staticmethod
    def VECTOR_ARTICLE_CONTENT_CHANGED(
        article_id: int, old_hash: str, new_hash: str
    ) -> str:
        return f"文章 {article_id} 内容已变化，将同步 (旧: {old_hash}, 新: {new_hash})"

    @staticmethod
    def VECTOR_ARTICLE_UNCHANGED(article_id: int) -> str:
        return f"文章 {article_id} 内容未变化，跳过同步"

    @staticmethod
    def VECTOR_SYNC_GET_ARTICLES_FAILED(error: Exception) -> str:
        return f"同步向量任务获取文章列表失败: {error}"

    @staticmethod
    def VECTOR_INCREMENTAL_SYNC_CHANGED(count: int) -> str:
        return f"增量同步模式：检测到 {count} 篇文章有变更"

    @staticmethod
    def VECTOR_FULL_SYNC_FOUND(count: int) -> str:
        return f"全量同步模式：找到 {count} 篇已发布文章"

    @staticmethod
    def VECTOR_DELETED_OLD_VECTORS(article_ids: str) -> str:
        return f"已删除旧向量 (IDs: {article_ids})"

    @staticmethod
    def VECTOR_DELETE_OLD_FAILED(error: Exception) -> str:
        return f"删除旧向量失败，将覆盖: {error}"

    @staticmethod
    def VECTOR_BATCH_SYNC_RETRY(
        batch_num: int, retry_count: int, max_retries: int, result: str
    ) -> str:
        return f"批次 {batch_num} 同步返回失败信息，准备重试 ({retry_count}/{max_retries}): {result}"

    @staticmethod
    def VECTOR_BATCH_RETRY_EXHAUSTED(max_retries: int, result: str) -> str:
        return f"重试 {max_retries} 次后仍然失败: {result}"

    @staticmethod
    def VECTOR_BATCH_SYNC_SUCCESS(batch_num: int, result: str) -> str:
        return f"批次 {batch_num} 同步成功: {result}"

    @staticmethod
    def VECTOR_BATCH_SYNC_FAILED_RETRY(
        batch_num: int, retry_count: int, max_retries: int, error: Exception
    ) -> str:
        return f"批次 {batch_num} 同步失败，准备重试 ({retry_count}/{max_retries}): {error}"

    @staticmethod
    def VECTOR_BATCH_RETRY_EXHAUSTED_ABANDON(
        batch_num: int, max_retries: int, error: Exception
    ) -> str:
        return f"批次 {batch_num} 重试 {max_retries} 次仍然失败，放弃同步: {error}"

    @staticmethod
    def VECTOR_SYNC_COMPLETED(
        sync_mode: str, total_synced: int, total_errors: int
    ) -> str:
        return f"{sync_mode}同步完成！成功: {total_synced} 篇，失败: {total_errors} 篇"

    @staticmethod
    def VECTOR_FAILED_ARTICLE_IDS(ids: str) -> str:
        return f"失败的文章 ID: {ids}"

    @staticmethod
    def VECTOR_SYNC_TASK_FAILED(error: Exception) -> str:
        return f"同步文章向量任务失败: {error}"

    @staticmethod
    def VECTOR_HASH_INIT_GET_ARTICLES_FAILED(error: Exception) -> str:
        return f"初始化 hash 缓存获取文章列表失败: {error}"

    @staticmethod
    def VECTOR_HASH_INIT_FOUND_ARTICLES(count: int) -> str:
        return f"找到 {count} 篇已发布文章，开始计算并缓存 hash..."

    @staticmethod
    def VECTOR_HASH_INIT_PROGRESS(count: int) -> str:
        return f"已初始化 {count} 篇文章的 hash 缓存..."

    @staticmethod
    def VECTOR_HASH_INIT_COMPLETE(initialized: int, skipped: int) -> str:
        return f"hash 缓存初始化完成！新增: {initialized} 篇，已存在: {skipped} 篇"

    @staticmethod
    def VECTOR_HASH_INIT_FAILED(error: Exception) -> str:
        return f"初始化文章 hash 缓存失败: {error}"

    # ===== Neo4j 同步任务模块 =====
    @staticmethod
    def NEO4J_SYNC_CLEANUP_COMPLETE(cleanup_result: Any) -> str:
        return f"[知识图谱] 删除同步清理完成: {cleanup_result}"

    @staticmethod
    def NEO4J_SYNC_FULL_COMPLETE(result: Any) -> str:
        return f"[知识图谱] 全量同步完成: {result}"

    # ===== RAG 结果格式化模块 =====
    @staticmethod
    def RAG_SEARCH_RESULT_HEADER(dedup_count: int, threshold: float) -> str:
        return f"找到 {dedup_count} 篇相关文章 (相似度阈值: {threshold}):\n\n"

    @staticmethod
    def RAG_RESULT_ARTICLE_LINE(index: int, article_id: Any, title: str) -> str:
        return f"{index}. 文章ID: {article_id}, 标题: {title}\n"

    @staticmethod
    def RAG_RESULT_SIMILARITY_SCORE(score: float) -> str:
        return f"   相似度分数: {score:.4f}\n"

    @staticmethod
    def RAG_RESULT_CONTENT_FRAGMENT(chunk_index: int, content_length: int) -> str:
        return f"   内容片段(第{chunk_index}块, 共{content_length}字):\n"

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
    RABBITMQ_CONNECTED_AUTO_RECONNECT: str = "RabbitMQ 连接成功（自动重连已启用）"
    RABBITMQ_RECONNECT_CHANNEL_RECOVERED: str = "RabbitMQ 重连成功，channel 已恢复"
    RABBITMQ_CLIENT_NOT_INITIALIZED_MESSAGE: str = "RabbitMQ 客户端未初始化"
    RABBITMQ_CONNECTION_CLOSED_MESSAGE: str = "RabbitMQ 连接已关闭"
    RABBITMQ_SEND_TO_QUEUE_SUCCESS: str = "RabbitMQ 消息已发送到队列"
    RABBITMQ_SEND_TO_QUEUE_FAILURE: str = "RabbitMQ 发送消息到队列失败"
    RABBITMQ_NOT_AVAILABLE: str = "日志装饰器捕获到异常，请检查日志详情"
    API_RABBITMQ_LOGGING_SUCCESS: str = "API 日志已发送到队列"
    API_RABBITMQ_LOGGING_FAILURE: str = "API 日志发送到队列失败"

    # ===== Redis =====
    REDIS_INITIALIZED_MESSAGE: str = "Redis 客户端初始化成功"

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

    @staticmethod
    def VECTOR_ENHANCE_SEARCH_TIMING(search_elapsed: float, result_count: int) -> str:
        return f"向量增强检索耗时: {search_elapsed:.3f}s, 结果数: {result_count}"

    @staticmethod
    def VECTOR_ENHANCE_SEARCH_SUCCESS(candidate_count: int, hit_count: int) -> str:
        return f"向量搜索增强成功，候选 {candidate_count} 篇，命中 {hit_count} 篇"

    @staticmethod
    def VECTOR_QUERY_CATEGORY(category_name: str) -> str:
        return f"分类: {category_name}"

    @staticmethod
    def VECTOR_QUERY_SUB_CATEGORY(sub_category_name: str) -> str:
        return f"子分类: {sub_category_name}"

    @staticmethod
    def VECTOR_QUERY_TAGS(tags_text: str) -> str:
        return f"标签: {tags_text}"

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
    UPDATE_ANALYZE_CACHES_ANALYZE_SERVICE_NONE_MESSAGE: str = (
        "update_analyze_caches: analyze_service 为 None，跳过缓存更新"
    )
    UPDATE_ANALYZE_CACHES_START_MESSAGE: str = "开始更新分析接口缓存"
    UPDATE_ANALYZE_CACHES_TOP10_START_MESSAGE: str = "更新前10篇文章缓存..."
    UPDATE_ANALYZE_CACHES_TOP10_SUCCESS_MESSAGE: str = "前10篇文章缓存更新成功"
    UPDATE_ANALYZE_CACHES_WORDCLOUD_START_MESSAGE: str = "更新词云图缓存..."
    UPDATE_ANALYZE_CACHES_WORDCLOUD_SUCCESS_MESSAGE: str = "词云图缓存更新成功"
    UPDATE_ANALYZE_CACHES_STATISTICS_START_MESSAGE: str = "更新文章统计信息缓存..."
    UPDATE_ANALYZE_CACHES_STATISTICS_SUCCESS_MESSAGE: str = "文章统计信息缓存更新成功"
    UPDATE_ANALYZE_CACHES_CATEGORY_STATISTICS_START_MESSAGE: str = (
        "更新按分类统计文章数量缓存..."
    )
    UPDATE_ANALYZE_CACHES_CATEGORY_STATISTICS_SUCCESS_MESSAGE: str = (
        "按分类统计文章数量缓存更新成功"
    )
    UPDATE_ANALYZE_CACHES_MONTHLY_STATISTICS_START_MESSAGE: str = (
        "更新月度文章发布统计缓存..."
    )
    UPDATE_ANALYZE_CACHES_MONTHLY_STATISTICS_SUCCESS_MESSAGE: str = (
        "月度文章发布统计缓存更新成功"
    )
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

    @staticmethod
    def GRAPH_SEARCH_NEO4J_EXCEPTION_LOG(error: Any) -> str:
        return f"Neo4j 查询异常: {error}"

    GRAPH_SEARCH_PATH_CANDIDATE: str = "Article-TAGGED_AS-Tag-TAGGED_AS-Article"

    GRAPH_SEARCH_PATH_FOLLOWED: str = "User-FOLLOWS-User-PUBLISHED_BY-Article"

    GRAPH_SEARCH_PATH_INTEREST: str = "User-LIKES-Article-TAGGED_AS-Tag"

    GRAPH_SEARCH_PATH_KEYWORD: str = "Article-TAGGED_AS-Tag"

    GRAPH_SEARCH_PATH_SUB_CATEGORY: str = (
        "User-LIKES|COLLECTS|COMMENTED_ON-Article-BELONGS_TO-SubCategory"
    )

    @staticmethod
    def GRAPH_SEARCH_QUERY_EXCEPTION_LOG(error: Any) -> str:
        return f"图谱信号查询异常: {error}"

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

    @staticmethod
    def NEO4J_TASK_FINISH_MESSAGE(result: Any) -> str:
        return f"[知识图谱任务] MySQL 到 Neo4j 同步完成: {result}"

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

    @staticmethod
    def SINGLEFLIGHT_KEY_HIT(key: str) -> str:
        return f"[singleflight] key={key} 命中回填缓存，复用首个请求结果"

    @staticmethod
    def SINGLEFLIGHT_KEY_START(key: str) -> str:
        return f"[singleflight] key={key} 开始执行缓存回源"

    @staticmethod
    def CACHE_GET_FAILED_DETAIL(func_name: str, error: Exception) -> str:
        return f"{func_name} 失败: {error}"

    @staticmethod
    def SERVICE_CACHE_HIT(service_name: str, duration: float) -> str:
        return f"{service_name}: [缓存命中] 耗时 {duration:.3f}s"

    @staticmethod
    def CACHE_FETCH_FAILED_WILL_QUERY_SOURCE(error: Exception) -> str:
        return f"缓存获取失败，将查询数据源: {error}"

    @staticmethod
    def SERVICE_CLICKHOUSE_DEGRADE_TO_DB(service_name: str, error: Exception) -> str:
        return f"{service_name}: ClickHouse 查询失败，降级为 DB: {error}"

    @staticmethod
    def SERVICE_CACHE_UPDATED(
        service_name: str, data_source: str, duration: float
    ) -> str:
        return f"{service_name}: {data_source} 数据已更新缓存，总耗时 {duration:.3f}s"

    @staticmethod
    def CACHE_UPDATE_FAILED_DETAIL(error: Exception) -> str:
        return f"更新缓存失败: {error}"

    @staticmethod
    def UPLOAD_FILE_TO_OSS_SUCCESS(oss_url: str) -> str:
        return f"文件上传成功，OSS地址: {oss_url}"

    @staticmethod
    def UPLOAD_FILE_TO_OSS_PATH_INFO(local_path: str, oss_path: str) -> str:
        return f"本地文件路径: {local_path}, OSS路径: {oss_path}"

    @staticmethod
    def UPLOAD_FILE_TO_OSS_REMOTE_FAILED(error: str) -> str:
        return f"远程上传文件到OSS失败: {error}"

    @staticmethod
    def WORDCLOUD_CACHE_MISS_WILL_RETRY(error: Exception) -> str:
        return f"获取词云图缓存失败，将重新生成: {error}"

    @staticmethod
    def WORDCLOUD_GENERATED_AND_CACHED(duration: float) -> str:
        return (
            f"get_wordcloud_service: 词云图已生成并缓存到L1+L2，总耗时 {duration:.3f}s"
        )

    @staticmethod
    def WORDCLOUD_CACHE_URL_FAILED(error: Exception) -> str:
        return f"缓存词云图URL失败: {error}"

    @staticmethod
    def EXPORT_ARTICLES_SUCCESS(file_path: str, total_rows: int) -> str:
        return f"文章表已导出到 {file_path}，共写入 {total_rows} 条记录"

    @staticmethod
    def STATISTICS_RESULT_INFO(statistics: Any) -> str:
        return f"获取文章统计信息: {statistics}"

    @staticmethod
    def CATEGORY_ARTICLE_COUNT_RESULT(
        total_categories: int, non_zero_count: int
    ) -> str:
        return f"get_category_article_count_service: 获取 {total_categories} 个大分类，有文章的分类数: {non_zero_count}"

    @staticmethod
    def MONTHLY_PUBLISH_COUNT_RESULT(month_count: int, article_month_count: int) -> str:
        return f"get_monthly_publish_count_service: 获取过去6个月中 {month_count} 个月份数据，有文章的月份数: {article_month_count}"

    REDIS_CONNECTION_FAILED_MESSAGE: str = "Redis 连接失败，无法获取上次同步时间戳"

    @staticmethod
    def REDIS_CONNECTION_FAILED(error: Exception) -> str:
        return f"[Redis] 连接失败: {error}"

    REDIS_CONNECTION_SAVE_FAILED_MESSAGE: str = "Redis 连接失败，无法保存同步时间戳"

    @staticmethod
    def REDIS_CLIENT_INITIALIZED(host: str, port: int, db: int) -> str:
        return f"[Redis] 客户端初始化成功: {host}:{port}/{db}"

    REDIS_COROUTINE_SYNC_EXECUTION_ERROR: str = (
        "Redis 协程不能在运行中的事件循环里直接同步执行"
    )

    REDIS_DATABASE_CLEARED_MESSAGE: str = "Redis数据库已清空"

    @staticmethod
    def REDIS_GET_FAILED(key: str, error: Exception) -> str:
        return f"[Redis] GET 失败 key={key}: {error}"

    @staticmethod
    def REDIS_SET_FAILED(key: str, error: Exception) -> str:
        return f"[Redis] SET 失败 key={key}: {error}"

    @staticmethod
    def REDIS_DELETE_FAILED(keys: tuple[str, ...], error: Exception) -> str:
        return f"[Redis] DELETE 失败 keys={keys}: {error}"

    @staticmethod
    def REDIS_EXISTS_FAILED(key: str, error: Exception) -> str:
        return f"[Redis] EXISTS 失败 key={key}: {error}"

    @staticmethod
    def REDIS_EXPIRE_FAILED(key: str, error: Exception) -> str:
        return f"[Redis] EXPIRE 失败 key={key}: {error}"

    @staticmethod
    def REDIS_TTL_FAILED(key: str, error: Exception) -> str:
        return f"[Redis] TTL 失败 key={key}: {error}"

    @staticmethod
    def REDIS_KEYS_FAILED(pattern: str, error: Exception) -> str:
        return f"[Redis] KEYS 失败 pattern={pattern}: {error}"

    @staticmethod
    def REDIS_FLUSHDB_FAILED(error: Exception) -> str:
        return f"[Redis] FLUSHDB 失败: {error}"

    @staticmethod
    def REDIS_LOCK_ACQUIRE_FAILED(lock_key: str, error: Exception) -> str:
        return f"[Redis] 获取分布式锁失败 key={lock_key}: {error}"

    @staticmethod
    def REDIS_LOCK_ACQUIRE_FAIL_MESSAGE(lock_key: str) -> str:
        return f"[分布式锁] 获取锁失败，跳过本次执行，key: {lock_key}"

    @staticmethod
    def REDIS_LOCK_ACQUIRE_SUCCESS_MESSAGE(lock_key: str) -> str:
        return f"[分布式锁] 获取锁成功，key: {lock_key}"

    @staticmethod
    def REDIS_LOCK_RELEASE_FAILED(lock_key: str, error: Exception) -> str:
        return f"[Redis] 释放分布式锁失败 key={lock_key}: {error}"

    @staticmethod
    def REDIS_LOCK_RELEASE_FAIL_MESSAGE(lock_key: str) -> str:
        return f"[分布式锁] 释放锁失败，key: {lock_key}"

    @staticmethod
    def REDIS_LOCK_RELEASE_SUCCESS_MESSAGE(lock_key: str) -> str:
        return f"[分布式锁] 释放锁成功，key: {lock_key}"

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
