from fastapi import FastAPI
from api.controller.testController import router as test_router
from api.controller.analyzeController import router as analyze_router
from api.controller.uploadController import router as upload_router
from api.controller.generateController import router as generate_router
from api.controller.chatController import router as chat_router
import uvicorn
from config.nacos import start_nacos
from config.config import load_config
from common.utils.logger import logger
from common.middleware.ContextMiddleware import ContextMiddleware
from common.handler.exception_handlers import global_exception_handler
from typing import Dict, Any

# TODO: COZE完成读取数据库的内容上传COZE知识库，并设置定时任务定时上传知识库，每小时1次
# TODO: COZE完成流式获取消息的优化

server_config: Dict[str, Any] = load_config("server")
IP: str = server_config["ip"]
PORT: int = server_config["port"]

app: FastAPI = FastAPI(
    title="FastAPI部分的Swagger文档集成",
    description="这是demo项目的FastAPI部分的Swagger文档集成",
    version="1.0.0")

app.add_middleware(ContextMiddleware)

app.add_exception_handler(Exception, global_exception_handler)

app.include_router(test_router)
app.include_router(analyze_router)
app.include_router(upload_router)
app.include_router(generate_router)
app.include_router(chat_router)

@app.on_event("startup")
def startup_event() -> None:
    start_nacos(port=PORT)
    logger.info(f"FastAPI应用已启动")
    logger.info(f"服务地址:http://{IP}:{PORT}")
    logger.info(f"Swagger文档地址: http://{IP}:{PORT}/docs")
    logger.info(f"ReDoc文档地址: http://{IP}:{PORT}/redoc")

if __name__ == "__main__":
    uvicorn.run("main:app", host=IP, port=PORT, reload=True)