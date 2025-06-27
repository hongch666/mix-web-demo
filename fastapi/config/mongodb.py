from pymongo import MongoClient
from pymongo.database import Database
from pymongo.mongo_client import MongoClient as MongoClientType

from config.config import load_config

URL: str = load_config("database")["mongodb"]["url"]
DATABASE: str = load_config("database")["mongodb"]["database"]

client: MongoClientType = MongoClient(URL)
db: Database = client[DATABASE]