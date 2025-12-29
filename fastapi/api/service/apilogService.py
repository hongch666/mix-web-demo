from functools import lru_cache
from typing import Any, Dict, List
from fastapi import Depends
from api.mapper import ApiLogMapper, get_apilog_mapper

class ApiLogService:
    """API 日志 Service"""

    def __init__(
            self, 
            api_log_mapper: ApiLogMapper = None
        ):
        self.mapper = api_log_mapper

    def get_api_average_response_time_service(self) -> List[Dict[str, Any]]:
        """
        获取所有接口的平均响应时间
        
        Returns:
            List[Dict]: 接口平均响应时间列表
        """
        return self.mapper.get_api_average_response_time_mapper()

    def get_called_count_apis_service(self) -> List[Dict[str, Any]]:
        """
        获取接口调用次数

        Returns:
            List[Dict]: 接口调用次数
        """
        return self.mapper.get_called_count_apis_mapper()

    def get_api_call_statistics_service(self) -> Dict[str, Any]:
        """
        获取 API 调用的整体统计信息
        
        Returns:
            Dict: 统计信息
        """
        return self.mapper.get_api_call_statistics_mapper()


@lru_cache()
def get_apilog_service(
        api_log_mapper: ApiLogMapper = Depends(get_apilog_mapper)
    ) -> ApiLogService:
    return ApiLogService(
        api_log_mapper
    )