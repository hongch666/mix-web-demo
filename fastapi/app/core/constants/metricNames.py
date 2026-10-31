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
