import traceback
from functools import lru_cache
from typing import Any, Optional

from app.core.base import Logger, LoggerProtocol
from app.core.constants import Messages
from app.internal.cache import (
    ApiLogCalledCountCache,
    ApiLogSpeedCache,
    get_api_log_called_count_cache,
    get_api_log_speed_cache,
)
from app.internal.clients import NestjsClient
from app.internal.crud import ApiLogMapper


class ApiLogService:
    """API 日志 Service：优先查询 ClickHouse ADS 层，失败或无数据时降级为远程调用，结果统一进两级缓存"""

    def __init__(
        self,
        nestjs_client: NestjsClient,
        api_log_mapper: ApiLogMapper,
        logger: LoggerProtocol | None = None,
        speed_cache: Optional[ApiLogSpeedCache] = None,
        called_count_cache: Optional[ApiLogCalledCountCache] = None,
    ) -> None:
        """注入 NestJS 客户端、API 日志 Mapper、日志器与两个结果缓存"""
        self._nestjs_client: NestjsClient = nestjs_client
        self._apiLogMapper: ApiLogMapper = api_log_mapper
        # 日志器可注入，缺省回退全局单例
        self._logger: LoggerProtocol = logger or Logger
        # 缓存缺省取单例，保证与依赖注入链路的实例一致
        self._speed_cache: ApiLogSpeedCache = speed_cache or get_api_log_speed_cache(
            self._logger
        )
        self._called_count_cache: ApiLogCalledCountCache = (
            called_count_cache or get_api_log_called_count_cache(self._logger)
        )

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

    async def _read_cache(self, cache: Any) -> Optional[list[dict[str, Any]]]:
        """读取结果缓存，缓存异常时按未命中处理"""
        try:
            cached: Optional[list[dict[str, Any]]] = await cache.get()
            if cached:
                self._logger.info(
                    Messages.SERVICE_CACHE_HIT(cache.__class__.__name__, 0)
                )
                return cached
            return None
        except Exception as error:
            self._logger.debug(
                Messages.CACHE_GET_FAILED_DETAIL(cache.__class__.__name__, error)
            )
            return None

    async def _write_cache(self, cache: Any, data: list[dict[str, Any]]) -> None:
        """把数仓或兜底的结果统一写入缓存，空结果与非缓存异常都不影响主流程"""
        if not data:
            return
        try:
            await cache.set(data)
        except Exception as error:
            self._logger.warning(Messages.CACHE_UPDATE_FAILED_DETAIL(error))

    async def get_api_average_response_time_service(self) -> list[dict[str, Any]]:
        """获取所有接口的平均响应时间，命中结果缓存时直接返回"""
        cached = await self._read_cache(self._speed_cache)
        if cached is not None:
            return cached

        result = await self._query_ads_with_fallback(
            self._apiLogMapper.get_api_average_speed_clickhouse_mapper_async,
            self._nestjs_client.get_api_average_speed,
        )
        await self._write_cache(self._speed_cache, result)
        return result

    async def get_called_count_apis_service(self) -> list[dict[str, Any]]:
        """获取接口调用次数，命中结果缓存时直接返回"""
        cached = await self._read_cache(self._called_count_cache)
        if cached is not None:
            return cached

        result = await self._query_ads_with_fallback(
            self._apiLogMapper.get_called_count_clickhouse_mapper_async,
            self._nestjs_client.get_called_count,
        )
        await self._write_cache(self._called_count_cache, result)
        return result


@lru_cache
def get_apilog_service(
    nestjs_client: NestjsClient,
    api_log_mapper: ApiLogMapper,
    logger: LoggerProtocol | None = None,
    speed_cache: Optional[ApiLogSpeedCache] = None,
    called_count_cache: Optional[ApiLogCalledCountCache] = None,
) -> ApiLogService:
    """按依赖参数缓存并返回 ApiLogService 单例"""
    return ApiLogService(
        nestjs_client, api_log_mapper, logger, speed_cache, called_count_cache
    )
