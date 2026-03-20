from typing import Any, Dict

import uvicorn
from app import create_app
from app.core.config import load_config

# 初始化 FastAPI 应用
app = create_app()

if __name__ == "__main__":
    # 获取 FastAPI 服务的端口和 IP 配置
    server_config: Dict[str, Any] = load_config("server")
    ip: str = server_config["ip"]
    port: int = server_config["port"]
    reload: bool = server_config["reload"]
    # 启动 uvicorn 服务器
    uvicorn.run("main:app", host=ip, port=port, reload=reload)
