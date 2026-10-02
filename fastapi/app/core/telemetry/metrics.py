from prometheus_client import Counter, Histogram

from app.core.constants import MetricNames

client_requests = Counter(
    MetricNames.CLIENT_REQUESTS,
    "下游服务调用次数",
    ["target_service", "method", "outcome"],
)
client_duration = Histogram(
    MetricNames.CLIENT_DURATION,
    "下游服务调用耗时",
    ["target_service", "method"],
)
task_runs = Counter(
    MetricNames.TASK_RUNS,
    "定时任务执行次数",
    ["task", "result"],
)
task_duration = Histogram(
    MetricNames.TASK_DURATION,
    "定时任务执行耗时",
    ["task"],
)
http_requests = Counter(
    MetricNames.HTTP_REQUESTS,
    "HTTP 请求次数",
    ["method", "route", "status"],
)
http_duration = Histogram(
    MetricNames.HTTP_DURATION,
    "HTTP 请求耗时",
    ["method", "route"],
)
