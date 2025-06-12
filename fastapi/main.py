from fastapi import FastAPI
from controller.testController import router as test_router
import uvicorn
from config.nacos import start_nacos
from config.config import load_config

# TODO: 对数据库的文章浏览量进行数据分析，获取前十名浏览量最高的文章
# TODO: 对日志中的搜索部分进行数据分析，根据搜索关键字进行词云图的生成（保存到本地）
# TODO: 使用上述数据进行机器学习分析，预测后续的文章应当使用的主题

server_config = load_config("server")
IP = server_config["ip"]
PORT = server_config["port"]

app = FastAPI(
    title="FastAPI部分的Swagger文档集成",
    description="这是demo项目的FastAPI部分的Swagger文档集成",
    version="1.0.0")

app.include_router(test_router)

@app.on_event("startup")
def startup_event():
    start_nacos(port=PORT)

if __name__ == "__main__":
    uvicorn.run("main:app", host=IP, port=PORT, reload=True)