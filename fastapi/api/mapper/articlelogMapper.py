from typing import Any, Dict, List
from config import db as mongo_db

def get_search_keywords_articlelog_mapper() -> List[str]:
    logs = mongo_db["articlelogs"]
    cursor = logs.find({"action": "search"})
    all_keywords: List[str] = []
    for log in cursor:
        content: Dict[str, Any] = log.get('content', {})
        if 'Keyword' in content:
            if content['Keyword'] == "":
                continue
            all_keywords.append(content['Keyword'])
    return all_keywords

def get_all_articlelogs_limit_mapper() -> List[Dict[str, Any]]:
    logs = mongo_db["articlelogs"]
    cursor: Any = logs.find().sort("createdAt", -1).limit(100)
    return cursor