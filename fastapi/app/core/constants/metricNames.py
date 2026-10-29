class MetricNames:
    """集中定义 HTTP、任务、数据库连接池、AI 与 RAG 等 Prometheus 监控指标名称的常量类"""

    # ===== HTTP 指标 =====

    HTTP_REQUESTS = "mix_http_requests_total"
    """HTTP 请求量计数器"""
    HTTP_DURATION = "mix_http_request_duration_seconds"
    """HTTP 请求耗时直方图"""
    # ===== 远程调用指标 =====

    CLIENT_REQUESTS = "mix_client_requests_total"
    """服务间调用量计数器"""
    CLIENT_DURATION = "mix_client_request_duration_seconds"
    """服务间调用耗时直方图"""
    # ===== 任务指标 =====

    TASK_RUNS = "mix_task_runs_total"
    """定时任务执行次数计数器"""
    TASK_DURATION = "mix_task_duration_seconds"
    """定时任务执行耗时直方图"""
    # ===== 资源与 AI 指标 =====

    DB_POOL_CONNECTIONS = "mix_db_pool_connections"
    """数据库连接池连接数仪表"""
    AI_CHAT = "mix_ai_chat_total"
    """AI 对话次数计数器"""
    AI_TOKENS = "mix_ai_tokens_total"
    """AI 对话消耗的 token 数计数器"""
    RAG_RETRIEVAL = "mix_rag_retrieval_total"
    """RAG 检索次数计数器"""
