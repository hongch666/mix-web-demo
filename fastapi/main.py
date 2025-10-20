import uvicorn
from fastapi import FastAPI
from typing import Dict, Any
from contextlib import asynccontextmanager
from api.controller import *
from api.service import get_embedding_service
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
        
        # 预加载嵌入模型（避免首次请求时下载）
        try:
            embedding_service = get_embedding_service()
            # 调用一次 encode_text 以触发模型加载
            embedding_service.encode_text("预加载模型")
            logger.info("嵌入模型已预加载")
        except Exception as e:
            logger.warning(f"嵌入模型预加载失败: {e}")
        
        # 启动Nacos服务注册
        start_nacos(ip=IP, port=PORT)
        
        # 启动定时任务调度器
        start_scheduler()
        
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

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host=IP, port=PORT, reload=True)