from fastapi.openapi.utils import get_openapi

from app.common.middleware import middlewares
from app.core.constants import SwaggerConfig
from app.core.errors import exception_handlers
from app.core.telemetry import instrument_fastapi
from app.core.telemetry.metrics import http_duration, http_requests
from app.internal.api import routers
from fastapi import FastAPI, Request
from time import perf_counter

from .lifespan import lifespan


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例

    Returns:
        FastAPI: 配置完成的 FastAPI 应用实例
    """
    app: FastAPI = FastAPI(
        title=SwaggerConfig.SWAGGER_TITLE,
        description=SwaggerConfig.SWAGGER_DESCRIPTION,
        version=SwaggerConfig.SWAGGER_VERSION,
        openapi_tags=SwaggerConfig.OPENAPI_TAGS,
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def record_http_metrics(request: Request, call_next):
        started_at: float = perf_counter()
        response = await call_next(request)
        route: str = getattr(request.scope.get("route"), "path", "UNKNOWN")
        http_requests.labels(request.method, route, str(response.status_code)).inc()
        http_duration.labels(request.method, route).observe(perf_counter() - started_at)
        return response

    instrument_fastapi(app)

    # 覆写 openapi 方法以设置 OpenAPI 版本
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=SwaggerConfig.OPENAPI_VERSION,
            description=app.description,
            routes=app.routes,
            tags=SwaggerConfig.OPENAPI_TAGS,
        )
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # 添加中间件
    for middleware in middlewares:
        app.add_middleware(middleware)

    # 添加异常处理器
    for exception_class, handler in exception_handlers.items():
        app.add_exception_handler(exception_class, handler)

    # 注册路由
    for router in routers:
        app.include_router(router)

    return app
