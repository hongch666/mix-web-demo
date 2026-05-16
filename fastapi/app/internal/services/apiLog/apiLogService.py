from functools import lru_cache
from typing import Any, Dict, List

from app.internal.clients import NestjsClient


class ApiLogService:
    """API 日志 Service"""

    def __init__(self) -> None:
        self._nestjs_client: NestjsClient = NestjsClient()

    async def get_api_average_response_time_service(self) -> List[Dict[str, Any]]:
        """
        获取所有接口的平均响应时间

        Returns:
            List[Dict]: 接口平均响应时间列表
        """
        return await self._nestjs_client.get_api_average_speed()

    async def get_called_count_apis_service(self) -> List[Dict[str, Any]]:
        """
        获取接口调用次数

        Returns:
            List[Dict]: 接口调用次数
        """
        return await self._nestjs_client.get_called_count_apis()

    async def get_api_call_statistics_service(self) -> Dict[str, Any]:
        """
        获取 API 调用的整体统计信息

        Returns:
            Dict: 统计信息
        """
        average_speed = await self._nestjs_client.get_api_average_speed()
        total_calls = sum(int(item.get("count", 0)) for item in average_speed)
        response_times = [
            float(item.get("avg_response_time", 0)) for item in average_speed
        ]
        return {
            "total_calls": total_calls,
            "avg_response_time": sum(response_times) / len(response_times)
            if response_times
            else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
        }


@lru_cache()
def get_apilog_service() -> ApiLogService:
    return ApiLogService()
