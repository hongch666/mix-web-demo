import asyncio
import traceback
from functools import lru_cache
from typing import Any

from app.core.base import Logger
from app.core.constants import Messages, WarehouseScripts
from app.core.db import ClickhouseConnectionPool, get_clickhouse_connection_pool


class ApiLogMapper:
    """API 日志 Mapper：直接查询 ClickHouse 数仓 ADS 层"""

    def __init__(self) -> None:
        self._clickhouse_pool: ClickhouseConnectionPool = (
            get_clickhouse_connection_pool()
        )

    async def _query_ads_async(
        self, query: str, columns: list[str]
    ) -> list[dict[str, Any]]:
        """执行 ADS 查询并转换为与远程聚合接口同构的字典列表"""
        ch_conn: Any = await self._clickhouse_pool.get_connection_async()
        try:
            results: Any = await asyncio.to_thread(ch_conn.execute, query)
            return [dict(zip(columns, row)) for row in results]
        except Exception as e:
            Logger.error(Messages.APILOG_CLICKHOUSE_QUERY_FAILED(e))
            Logger.debug(traceback.format_exc())
            raise
        finally:
            if ch_conn:
                await self._clickhouse_pool.return_connection_async(ch_conn)

    async def get_api_average_speed_clickhouse_mapper_async(
        self,
    ) -> list[dict[str, Any]]:
        """从 ADS 层获取接口平均响应速度"""
        return await self._query_ads_async(
            WarehouseScripts.API_AVERAGE_SPEED_QUERY,
            [
                "api_path",
                "api_method",
                "api_description",
                "avg_response_time",
                "call_count",
            ],
        )

    async def get_called_count_clickhouse_mapper_async(
        self,
    ) -> list[dict[str, Any]]:
        """从 ADS 层获取接口调用次数"""
        return await self._query_ads_async(
            WarehouseScripts.API_CALLED_COUNT_QUERY,
            [
                "api_path",
                "api_method",
                "api_description",
                "call_count",
                "avg_response_time",
            ],
        )


@lru_cache()
def get_api_log_mapper() -> ApiLogMapper:
    """获取 ApiLogMapper 单例实例"""
    return ApiLogMapper()
