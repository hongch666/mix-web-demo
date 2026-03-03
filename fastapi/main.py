from typing import Any

import uvicorn
from app import create_app
from app.db import load_config

app = create_app()

if __name__ == "__main__":
    server_config: dict[str, Any] = load_config("server")
    ip = server_config["ip"]
    port = server_config["port"]
    reload = server_config["reload"]
    uvicorn.run("main:app", host=ip, port=port, reload=reload)
