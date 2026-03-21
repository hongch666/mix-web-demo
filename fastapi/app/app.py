from app.common.middleware import middlewares
from app.core.base import Constants
from app.core.errors import exception_handlers
from app.internal.api import routers
from app.lifespan import lifespan
from fastapi import FastAPI


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例

    Returns:
        FastAPI: 配置完成的 FastAPI 应用实例
    """
    app: FastAPI = FastAPI(
        title=Constants.SWAGGER_TITLE,
        description=Constants.SWAGGER_DESCRIPTION,
        version=Constants.SWAGGER_VERSION,
        lifespan=lifespan,
    )

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
