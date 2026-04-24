from functools import lru_cache
from typing import Any, Dict, List

from app.core.db import async_db as mongo_db


class ApiLogMapper:
    """API 日志 Mapper"""

    def __init__(self) -> None:
        self.logs = mongo_db["apilogs"]

    async def get_api_average_response_time_mapper(self) -> List[Dict[str, Any]]:
        """
        获取所有接口的平均响应时间
        按照 api_path 和 api_method 分组

        Returns:
            List[Dict]: 包含接口路径、方法和平均响应时间的列表
        """

        # MongoDB 聚合查询
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "api_path": "$apiPath",
                        "api_method": "$apiMethod",
                        "api_description": "$apiDescription",
                    },
                    "avg_response_time": {"$avg": "$responseTime"},
                    "count": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "api_path": "$_id.api_path",
                    "api_method": "$_id.api_method",
                    "api_description": "$_id.api_description",
                    "avg_response_time": {"$round": ["$avg_response_time", 2]},
                    "count": 1,
                }
            },
            {"$sort": {"avg_response_time": -1}},
        ]

        cursor = self.logs.aggregate(pipeline)
        return await cursor.to_list(length=None)

    async def get_called_count_apis_mapper(self) -> List[Dict[str, Any]]:
        """
        获取接口调用次数
        按照 api_path 和 api_method 分组

        Returns:
            List[Dict]: 包含接口路径、方法和调用次数的前10个接口
        """

        # MongoDB 聚合查询
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "api_path": "$apiPath",
                        "api_method": "$apiMethod",
                        "api_description": "$apiDescription",
                    },
                    "call_count": {"$sum": 1},
                    "avg_response_time": {"$avg": "$responseTime"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "api_path": "$_id.api_path",
                    "api_method": "$_id.api_method",
                    "api_description": "$_id.api_description",
                    "call_count": 1,
                    "avg_response_time": {"$round": ["$avg_response_time", 2]},
                }
            },
            {"$sort": {"call_count": -1}},
        ]

        cursor = self.logs.aggregate(pipeline)
        return await cursor.to_list(length=None)

    async def get_api_call_statistics_mapper(self) -> Dict[str, Any]:
        """获取 API 调用的整体统计信息。"""

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
