from typing import Callable, Dict, List, Type

from app.api import (
    aiHistoryRouter,
    analyzeRouter,
    apiLogRouter,
    chatRouter,
    generateRouter,
    testRouter,
    uploadRouter,
    userRouter,
)
from app.core.errors.exceptionHandlers import exception_handlers
from app.lifespan import lifespan
from app.middleware import middlewares
from fastapi import APIRouter, FastAPI


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例

    Returns:
        FastAPI: 配置完成的 FastAPI 应用实例
    """
    app: FastAPI = FastAPI(lifespan=lifespan)

    # 添加中间件
    middleware_list: List[Callable] = middlewares
    for middleware in middleware_list:
        app.add_middleware(middleware)

    # 添加异常处理器
    exception_handlers_dict: Dict[Type[Exception], Callable] = exception_handlers
    for exception_class, handler in exception_handlers_dict.items():
        app.add_exception_handler(exception_class, handler)

    # 注册路由
    routers: List[APIRouter] = [
        analyzeRouter,
        apiLogRouter,
        chatRouter,
        generateRouter,
        testRouter,
        uploadRouter,
        aiHistoryRouter,
        userRouter,
    ]
    for router in routers:
        app.include_router(router)

    return app
