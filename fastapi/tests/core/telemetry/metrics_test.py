from prometheus_client import REGISTRY

from app.core.constants import MetricNames
from app.core.telemetry.metrics import (
    client_duration,
    client_requests,
    http_duration,
    http_requests,
    task_duration,
    task_runs,
)


def _sample_value(sample_name: str, labels: dict[str, str]) -> float:
    """读取样本当前值, 未命中标签组合时按 0 处理以便用增量断言"""
    value = REGISTRY.get_sample_value(sample_name, labels)
    return value or 0.0


# 客户端指标按 (target_service, method, outcome) 与 (target_service, method) 的位置打点
def test_client_metrics_record_client_label_positions() -> None:
    request_labels = {"target_service": "spring", "method": "GET", "outcome": "success"}
    duration_labels = {"target_service": "spring", "method": "GET"}
    before_requests = _sample_value(MetricNames.CLIENT_REQUESTS, request_labels)
    before_duration = _sample_value(
        MetricNames.CLIENT_DURATION + "_count", duration_labels
    )

    client_requests.labels("spring", "GET", "success").inc()
    client_duration.labels("spring", "GET").observe(0.01)

    assert _sample_value(MetricNames.CLIENT_REQUESTS, request_labels) == (
        before_requests + 1
    )
    assert _sample_value(MetricNames.CLIENT_DURATION + "_count", duration_labels) == (
        before_duration + 1
    )


# 定时任务指标按 (task, result) 与 (task) 的位置打点
def test_task_metrics_record_task_label_positions() -> None:
    run_labels = {"task": "es-sync", "result": "success"}
    duration_labels = {"task": "es-sync"}
    before_runs = _sample_value(MetricNames.TASK_RUNS, run_labels)
    before_duration = _sample_value(
        MetricNames.TASK_DURATION + "_count", duration_labels
    )

    task_runs.labels("es-sync", "success").inc()
    task_duration.labels("es-sync").observe(0.01)

    assert _sample_value(MetricNames.TASK_RUNS, run_labels) == before_runs + 1
    assert _sample_value(MetricNames.TASK_DURATION + "_count", duration_labels) == (
        before_duration + 1
    )


# HTTP 指标按 (method, route, status) 与 (method, route) 的位置打点
def test_http_metrics_record_request_label_positions() -> None:
    request_labels = {"method": "GET", "route": "/users", "status": "200"}
    duration_labels = {"method": "GET", "route": "/users"}
    before_requests = _sample_value(MetricNames.HTTP_REQUESTS, request_labels)
    before_duration = _sample_value(
        MetricNames.HTTP_DURATION + "_count", duration_labels
    )

    http_requests.labels("GET", "/users", "200").inc()
    http_duration.labels("GET", "/users").observe(0.01)

    assert _sample_value(MetricNames.HTTP_REQUESTS, request_labels) == (
        before_requests + 1
    )
    assert _sample_value(MetricNames.HTTP_DURATION + "_count", duration_labels) == (
        before_duration + 1
    )
