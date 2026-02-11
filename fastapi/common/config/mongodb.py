from pymongo import MongoClient
from pymongo.database import Database
from pymongo.mongo_client import MongoClient as MongoClientType

from common.config import load_config

# 从配置文件读取 MongoDB 连接信息
mongo_config = load_config("database")["mongodb"]
host = mongo_config["host"]
port = mongo_config["port"]
username = mongo_config.get("username")
password = mongo_config.get("password")
DATABASE: str = mongo_config["database"]

# 根据是否有用户名和密码构建 URI
if username and password:
    URL: str = f"mongodb://{username}:{password}@{host}:{port}"
else:
    URL: str = f"mongodb://{host}:{port}"

client: MongoClientType = MongoClient(URL)
db: Database = client[DATABASE]