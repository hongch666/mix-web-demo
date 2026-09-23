import traceback
from functools import lru_cache
from typing import Any

from app.core.base import Logger
from app.core.constants import Messages
from app.internal.clients import NestjsClient
from app.internal.crud import ApiLogMapper


class ApiLogService:
    """API 日志 Service：优先查询 ClickHouse ADS 层，失败或无数据时降级为远程调用"""

    def __init__(
        self,
        nestjs_client: NestjsClient,
        api_log_mapper: ApiLogMapper,
    ) -> None:
        self._nestjs_client: NestjsClient = nestjs_client
        self._apiLogMapper: ApiLogMapper = api_log_mapper

    async def _query_ads_with_fallback(
        self,
        ads_loader: Any,
        remote_loader: Any,
    ) -> list[dict[str, Any]]:
        """先查 ClickHouse ADS 层，异常或空结果时降级为远程聚合查询（兜底）"""
        try:
            result: list[dict[str, Any]] = await ads_loader()
            if result:
                Logger.info(Messages.APILOG_ADS_SOURCE)
                return result
            Logger.info(Messages.APILOG_ADS_EMPTY_FALLBACK_REMOTE)
        except Exception as error:
            Logger.error(Messages.APILOG_CLICKHOUSE_QUERY_FAILED(error))
            Logger.debug(traceback.format_exc())
        return await remote_loader()

    async def get_api_average_response_time_service(self) -> list[dict[str, Any]]:
        """获取所有接口的平均响应时间"""
        return await self._query_ads_with_fallback(
            self._apiLogMapper.get_api_average_speed_clickhouse_mapper_async,
            self._nestjs_client.get_api_average_speed,
        )

    async def get_called_count_apis_service(self) -> list[dict[str, Any]]:
        """获取接口调用次数"""
        return await self._query_ads_with_fallback(
            self._apiLogMapper.get_called_count_clickhouse_mapper_async,
            self._nestjs_client.get_called_count,
        )


@lru_cache
def get_apilog_service(
    nestjs_client: NestjsClient,
    api_log_mapper: ApiLogMapper,
) -> ApiLogService:
    return ApiLogService(nestjs_client, api_log_mapper)
