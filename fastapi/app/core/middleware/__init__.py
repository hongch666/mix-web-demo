from starlette.middleware.base import BaseHTTPMiddleware

from .contextMiddleware import (
    ContextMiddleware,
    get_current_internal_token,
    get_current_session_id,
    get_current_token,
    get_current_trace_id,
    get_current_user_id,
    get_current_username,
)
from .metricsMiddleware import MetricsMiddleware

# add_middleware 会把后注册的中间件放到最外层，因此列表按「内层 → 外层」声明：
# MetricsMiddleware 在内（只统计路由与处理耗时），ContextMiddleware 在外（请求进入即写入上下文）
middlewares: list[type[BaseHTTPMiddleware]] = [MetricsMiddleware, ContextMiddleware]

__all__: list[str] = [
    "ContextMiddleware",
    "MetricsMiddleware",
    "get_current_user_id",
    "get_current_username",
    "get_current_session_id",
    "get_current_token",
    "get_current_internal_token",
    "get_current_trace_id",
    "middlewares",
]
