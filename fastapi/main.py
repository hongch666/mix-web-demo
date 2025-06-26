from fastapi import FastAPI
from api.controller.testController import router as test_router
from api.controller.analyzeController import router as analyze_router
from api.controller.uploadController import router as upload_router
from api.controller.generateController import router as generate_router
import uvicorn
from config.nacos import start_nacos
from config.config import load_config
from common.middleware.ContextMiddleware import ContextMiddleware
from common.handler.exception_handlers import global_exception_handler

# TODO: 终端日志保存到专门的日志文件中
# TODO: 接入COZE平台

server_config = load_config("server")
IP = server_config["ip"]
PORT = server_config["port"]

app = FastAPI(
    title="FastAPI部分的Swagger文档集成",
    description="这是demo项目的FastAPI部分的Swagger文档集成",
    version="1.0.0")

app.add_middleware(ContextMiddleware)

app.add_exception_handler(Exception, global_exception_handler)

app.include_router(test_router)
app.include_router(analyze_router)
app.include_router(upload_router)
app.include_router(generate_router)

@app.on_event("startup")
def startup_event():
    start_nacos(port=PORT)

if __name__ == "__main__":
    uvicorn.run("main:app", host=IP, port=PORT, reload=True)