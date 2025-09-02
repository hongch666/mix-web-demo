from fastapi import FastAPI
from api.controller import generate_router, chat_router
import uvicorn
from config import start_nacos, load_config
from common.utils import logger
from common.middleware import ContextMiddleware
from common.handler import global_exception_handler
from typing import Dict, Any
from contextlib import asynccontextmanager

server_config: Dict[str, Any] = load_config("server")
IP: str = server_config["ip"]
PORT: int = server_config["port"]

def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        start_nacos(port=PORT)
        logger.info(f"FastAPI应用已启动")
        logger.info(f"服务地址:http://{IP}:{PORT}")
        logger.info(f"Swagger文档地址: http://{IP}:{PORT}/docs")
        logger.info(f"ReDoc文档地址: http://{IP}:{PORT}/redoc")
        yield

    app = FastAPI(
        title="FastAPI部分的Swagger文档集成",
        description="这是demo项目的FastAPI部分的Swagger文档集成",
        version="1.0.0",
        lifespan=lifespan
    )
    app.add_middleware(ContextMiddleware)
    app.add_exception_handler(Exception, global_exception_handler)
    app.include_router(generate_router)
    app.include_router(chat_router)
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host=IP, port=PORT, reload=True)