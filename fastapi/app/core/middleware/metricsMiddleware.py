from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.telemetry.metrics import http_duration, http_requests


class MetricsMiddleware(BaseHTTPMiddleware):
    """HTTP 指标中间件，按路由统计每个请求的调用次数与响应耗时"""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """统计请求指标：调用次数按方法、路由与状态码打点，响应耗时按方法与路由记录

        路由取自请求作用域的 route（未命中路由时记为 UNKNOWN），因此必须在
        call_next 返回之后再读取
        """
        started_at: float = perf_counter()
        response: Response = await call_next(request)
        route: str = getattr(request.scope.get("route"), "path", "UNKNOWN")
        http_requests.labels(request.method, route, str(response.status_code)).inc()
        http_duration.labels(request.method, route).observe(perf_counter() - started_at)
        return response
