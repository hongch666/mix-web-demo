import uvicorn
from fastapi import FastAPI
from typing import Dict, Any
from contextlib import asynccontextmanager
from api.controller import *
from config import start_nacos, load_config, create_tables
from common.utils import logger
from common.middleware import ContextMiddleware
from common.handler import global_exception_handler
from common.task import start_scheduler


server_config: Dict[str, Any] = load_config("server")
IP: str = server_config["ip"]
PORT: int = server_config["port"]

def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # 自动建表
        create_tables(['ai_history'])
        # 启动Nacos服务注册
        start_nacos(ip=IP, port=PORT)
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
    app.include_router(test_router)
    app.include_router(analyze_router)
    app.include_router(upload_router)
    app.include_router(generate_router)
    app.include_router(chat_router)
    app.include_router(ai_history_router)
    return app

start_scheduler()
app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host=IP, port=PORT, reload=True)