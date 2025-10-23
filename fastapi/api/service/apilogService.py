from functools import lru_cache
from typing import Any, Dict, List
from api.mapper import get_apilog_mapper


class ApiLogService:
    """API 日志 Service"""

    def __init__(self):
        self.mapper = get_apilog_mapper()

    def get_api_average_response_time_service(self) -> List[Dict[str, Any]]:
        """
        获取所有接口的平均响应时间
        
        Returns:
            List[Dict]: 接口平均响应时间列表
        """
        return self.mapper.get_api_average_response_time_mapper()

    def get_top10_most_called_apis_service(self) -> List[Dict[str, Any]]:
        """
        获取调用次数最多的前10个接口
        
        Returns:
            List[Dict]: 前10个最常调用的接口
        """
        return self.mapper.get_top10_most_called_apis_mapper()

    def get_api_call_statistics_service(self) -> Dict[str, Any]:
        """
        获取 API 调用的整体统计信息
        
        Returns:
            Dict: 统计信息
        """
        return self.mapper.get_api_call_statistics_mapper()


@lru_cache()
def get_apilog_service() -> ApiLogService:
    return ApiLogService()
