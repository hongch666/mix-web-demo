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
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    for middleware in middlewares:
        app.add_middleware(middleware)

    for exception_class, handler in exception_handlers.items():
        app.add_exception_handler(exception_class, handler)

    for router in [
        analyzeRouter,
        apiLogRouter,
        chatRouter,
        generateRouter,
        testRouter,
        uploadRouter,
        aiHistoryRouter,
        userRouter,
    ]:
        app.include_router(router)

    return app
