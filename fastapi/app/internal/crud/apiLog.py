from functools import lru_cache
from typing import Any

from sqlalchemy import desc, select

from app.core.constants import Messages
from app.core.db import ClickHouseSessionFactory
from app.internal.models import AdsApiAverageSpeed, AdsApiCalledCount


class ApiLogMapper:
    """API 日志数仓 Mapper，查询使用 SQLAlchemy ClickHouse ORM"""

    def __init__(self, session_factory: ClickHouseSessionFactory) -> None:
        self._session_factory = session_factory

    async def _execute_mappings(self, statement: Any) -> list[dict[str, Any]]:
        async with self._session_factory() as session:
            result = await session.execute(statement)
            return [dict(row) for row in result.mappings().all()]

    async def get_api_average_speed_clickhouse_mapper_async(
        self,
    ) -> list[dict[str, Any]]:
        statement = select(
            AdsApiAverageSpeed.api_path,
            AdsApiAverageSpeed.api_method,
            AdsApiAverageSpeed.api_description,
            AdsApiAverageSpeed.avg_response_time,
            AdsApiAverageSpeed.call_count,
        ).order_by(desc(AdsApiAverageSpeed.avg_response_time))
        try:
            return await self._execute_mappings(statement)
        except Exception as error:
            raise RuntimeError(Messages.APILOG_CLICKHOUSE_QUERY_FAILED(error)) from error

    async def get_called_count_clickhouse_mapper_async(
        self,
    ) -> list[dict[str, Any]]:
        statement = select(
            AdsApiCalledCount.api_path,
            AdsApiCalledCount.api_method,
            AdsApiCalledCount.api_description,
            AdsApiCalledCount.call_count,
            AdsApiCalledCount.avg_response_time,
        ).order_by(desc(AdsApiCalledCount.call_count))
        try:
            return await self._execute_mappings(statement)
        except Exception as error:
            raise RuntimeError(Messages.APILOG_CLICKHOUSE_QUERY_FAILED(error)) from error


@lru_cache()
def get_api_log_mapper(session_factory: ClickHouseSessionFactory) -> ApiLogMapper:
    return ApiLogMapper(session_factory)
