from fastapi import FastAPI
from controller.testController import router as test_router
from controller.analyzeController import router as analyze_router
import uvicorn
from config.nacos import start_nacos
from config.config import load_config

# TODO: 将词云图保存到阿里云，并返回阿里云的图片地址
# TODO: 使用上述数据进行机器学习分析，预测后续的文章的浏览量，预测top10的文章，预测未来的搜索关键词或主题

server_config = load_config("server")
IP = server_config["ip"]
PORT = server_config["port"]

app = FastAPI(
    title="FastAPI部分的Swagger文档集成",
    description="这是demo项目的FastAPI部分的Swagger文档集成",
    version="1.0.0")

app.include_router(test_router)
app.include_router(analyze_router)

@app.on_event("startup")
def startup_event():
    start_nacos(port=PORT)

if __name__ == "__main__":
    uvicorn.run("main:app", host=IP, port=PORT, reload=True)