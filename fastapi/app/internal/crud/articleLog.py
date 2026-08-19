from functools import lru_cache
from typing import Any, Dict, List

from app.core.db import async_db as mongo_db


class ArticleLogMapper:
    """文章日志 Mapper"""

    async def get_search_keywords_articlelog_mapper(self) -> List[str]:
        logs: Any = mongo_db["articlelogs"]
        pipeline = [
            {"$match": {"action": "search"}},
            {"$project": {"keyword": "$content.Keyword"}},
            {"$match": {"keyword": {"$ne": "", "$exists": True}}},
            {"$group": {"_id": "$keyword"}},
            {"$sort": {"_id": 1}},
        ]
        cursor: Any = logs.aggregate(pipeline)
        results: List[Dict[str, Any]] = await cursor.to_list(length=None)
        all_keywords: List[str] = [doc["_id"] for doc in results]
        return all_keywords


@lru_cache()
def get_articlelog_mapper() -> ArticleLogMapper:
    return ArticleLogMapper()
