from functools import lru_cache
from typing import Any, Dict, List
from config import db as mongo_db

class ArticleLogMapper:
    def get_search_keywords_articlelog_mapper(self) -> List[str]:
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

    def get_all_articlelogs_limit_mapper(self) -> List[Dict[str, Any]]:
        logs = mongo_db["articlelogs"]
        cursor: Any = logs.find().sort("createdAt", -1).limit(100)
        return cursor

@lru_cache()
def get_articlelog_mapper() -> ArticleLogMapper:
    return ArticleLogMapper()