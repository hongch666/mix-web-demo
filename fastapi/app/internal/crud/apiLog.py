from functools import lru_cache
from typing import Any, Dict, List

from app.core.db import async_db as mongo_db


class ApiLogMapper:
    """API 日志 Mapper"""

    def __init__(self) -> None:
        self.logs = mongo_db["apilogs"]

    async def get_api_call_statistics_mapper(self) -> Dict[str, Any]:
        """获取 API 调用的整体统计信息"""

        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_calls": {"$sum": 1},
                    "avg_response_time": {"$avg": "$responseTime"},
                    "max_response_time": {"$max": "$responseTime"},
                    "min_response_time": {"$min": "$responseTime"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "total_calls": 1,
                    "avg_response_time": {"$round": ["$avg_response_time", 2]},
                    "max_response_time": {"$round": ["$max_response_time", 2]},
                    "min_response_time": {"$round": ["$min_response_time", 2]},
                }
            },
        ]

        cursor = self.logs.aggregate(pipeline)
        results = await cursor.to_list(length=1)
        if results:
            return results[0]

        return {
            "total_calls": 0,
            "avg_response_time": 0,
            "max_response_time": 0,
            "min_response_time": 0,
        }


@lru_cache()
def get_apilog_mapper() -> ApiLogMapper:
    return ApiLogMapper()
