import uvicorn
from typing import Dict, Any
from api.app import create_app
from config import load_config

app = create_app()

if __name__ == "__main__":
    # 获取服务信息
    server_config: Dict[str, Any] = load_config("server")
    ip: str = server_config["ip"]
    port: int = server_config["port"]
    reload: bool = server_config["reload"]
    # 启动 uvicorn 服务器
    uvicorn.run("main:app", host=ip, port=port, reload=reload)