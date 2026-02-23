from typing import Any, Dict

import uvicorn
from api import create_app
from common.config import load_config

# 初始化app
app = create_app()

if __name__ == "__main__":
    # 获取 FastAPI 服务的端口和IP
    server_config: Dict[str, Any] = load_config("server")
    ip: str = server_config["ip"]
    port: int = server_config["port"]
    reload: bool = server_config["reload"]
    # 启动 uvicorn 服务器
    uvicorn.run("main:app", host=ip, port=port, reload=reload)
