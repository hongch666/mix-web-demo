from functools import lru_cache
from typing import Any, Dict, List
from common.config import db as mongo_db

class ApiLogMapper:
    """API 日志 Mapper"""
    
    def __init__(self) -> None:
        self.logs = mongo_db["apilogs"]

    def get_api_average_response_time_mapper(self) -> List[Dict[str, Any]]:
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
                        "api_description": "$apiDescription"
                    },
                    "avg_response_time": {"$avg": "$responseTime"},
                    "count": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "api_path": "$_id.api_path",
                    "api_method": "$_id.api_method",
                    "api_description": "$_id.api_description",
                    "avg_response_time": {"$round": ["$avg_response_time", 2]},
                    "count": 1
                }
            },
            {
                "$sort": {"avg_response_time": -1}
            }
        ]
        
        cursor = self.logs.aggregate(pipeline)
        return list(cursor)

    def get_called_count_apis_mapper(self) -> List[Dict[str, Any]]:
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
                        "api_description": "$apiDescription"
                    },
                    "call_count": {"$sum": 1},
                    "avg_response_time": {"$avg": "$responseTime"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "api_path": "$_id.api_path",
                    "api_method": "$_id.api_method",
                    "api_description": "$_id.api_description",
                    "call_count": 1,
                    "avg_response_time": {"$round": ["$avg_response_time", 2]}
                }
            },
            {
                "$sort": {"call_count": -1}
            }
        ]
        
        cursor = self.logs.aggregate(pipeline)
        return list(cursor)


@lru_cache()
def get_apilog_mapper() -> ApiLogMapper:
    return ApiLogMapper()
