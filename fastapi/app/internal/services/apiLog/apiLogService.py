from functools import lru_cache
from typing import Any, Dict, List

from app.internal.clients import NestjsClient


class ApiLogService:
    """API 日志 Service"""

    def __init__(self) -> None:
        self._nestjs_client: NestjsClient = NestjsClient()

    async def get_api_average_response_time_service(self) -> List[Dict[str, Any]]:
        """获取所有接口的平均响应时间"""
        return await self._nestjs_client.get_api_average_speed()

    async def get_called_count_apis_service(self) -> List[Dict[str, Any]]:
        """获取接口调用次数"""
        return await self._nestjs_client.get_called_count()


@lru_cache()
def get_apilog_service() -> ApiLogService:
    return ApiLogService()
