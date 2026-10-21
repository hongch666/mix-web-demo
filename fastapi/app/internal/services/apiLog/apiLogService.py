import traceback
from functools import lru_cache
from typing import Any

from app.core.base import Logger, LoggerProtocol
from app.core.constants import Messages
from app.internal.clients import NestjsClient
from app.internal.crud import ApiLogMapper


class ApiLogService:
    """API 日志 Service：优先查询 ClickHouse ADS 层，失败或无数据时降级为远程调用"""

    def __init__(
        self,
        nestjs_client: NestjsClient,
        api_log_mapper: ApiLogMapper,
        logger: LoggerProtocol | None = None,
    ) -> None:
        """注入 NestJS 客户端、API 日志 Mapper 与日志器"""
        self._nestjs_client: NestjsClient = nestjs_client
        self._apiLogMapper: ApiLogMapper = api_log_mapper
        # 日志器可注入，缺省回退全局单例
        self._logger: LoggerProtocol = logger or Logger

    async def _query_ads_with_fallback(
        self,
        ads_loader: Any,
        remote_loader: Any,
    ) -> list[dict[str, Any]]:
        """先查 ClickHouse ADS 层，异常或空结果时降级为远程聚合查询（兜底）"""
        try:
            result: list[dict[str, Any]] = await ads_loader()
            if result:
                self._logger.info(Messages.APILOG_ADS_SOURCE)
                return result
            self._logger.info(Messages.APILOG_ADS_EMPTY_FALLBACK_REMOTE)
        except Exception as error:
            self._logger.error(Messages.APILOG_CLICKHOUSE_QUERY_FAILED(error))
            self._logger.debug(traceback.format_exc())
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
    logger: LoggerProtocol | None = None,
) -> ApiLogService:
    """按依赖参数缓存并返回 ApiLogService 单例"""
    return ApiLogService(nestjs_client, api_log_mapper, logger)
