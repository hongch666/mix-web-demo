from typing import Any, Dict

from app.core.config.config import load_config
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# 从配置文件读取 MongoDB 连接信息
mongo_config: Dict[str, Any] = load_config("database")["mongodb"]
host: str = mongo_config["host"]
port: int = mongo_config["port"]
username: str | None = mongo_config.get("username")
password: str | None = mongo_config.get("password")
DATABASE: str = mongo_config["database"]

# 根据是否有用户名和密码构建 URI
if username and password:
    URL: str = f"mongodb://{username}:{password}@{host}:{port}"
else:
    URL: str = f"mongodb://{host}:{port}"

async_client: AsyncIOMotorClient = AsyncIOMotorClient(URL)
async_db: AsyncIOMotorDatabase = async_client[DATABASE]
