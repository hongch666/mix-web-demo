from fastapi.openapi.utils import get_openapi

from app.common.middleware import middlewares
from app.core.constants import Messages
from app.core.errors import exception_handlers
from app.internal.api import routers
from fastapi import FastAPI

from .lifespan import lifespan


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例

    Returns:
        FastAPI: 配置完成的 FastAPI 应用实例
    """
    app: FastAPI = FastAPI(
        title=Messages.SWAGGER_TITLE,
        description=Messages.SWAGGER_DESCRIPTION,
        version=Messages.SWAGGER_VERSION,
        openapi_tags=Messages.OPENAPI_TAGS,
        lifespan=lifespan,
    )

    # 覆写 openapi 方法以设置 OpenAPI 版本
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=Messages.OPENAPI_VERSION,
            description=app.description,
            routes=app.routes,
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
