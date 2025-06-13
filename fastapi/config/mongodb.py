from pymongo import MongoClient

from config.config import load_config

URL = load_config("database")["mongodb"]["url"]
DATABASE = load_config("database")["mongodb"]["database"]

client = MongoClient(URL)
db = client[DATABASE]