from fastapi import FastAPI
from controller.testController import router as test_router
import uvicorn

# TODO: 完成Nacos服务注册与发现，和服务间的调用
# TODO: 完成对本地大模型的调用和接口暴露
# TODO: 提取出公共的yaml配置文件，完成配置的统一管理

app = FastAPI()

app.include_router(test_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8084, reload=True)