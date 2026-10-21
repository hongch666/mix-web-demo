from functools import lru_cache
from typing import Any

from sqlalchemy import desc, select

from app.core.constants import Messages
from app.core.db import ClickHouseSessionFactory
from app.internal.models import AdsApiAverageSpeed, AdsApiCalledCount


class ApiLogMapper:
    """API 日志数仓 Mapper，查询使用 SQLAlchemy ClickHouse ORM"""

    def __init__(self, session_factory: ClickHouseSessionFactory) -> None:
        """保存 ClickHouse 会话工厂供各数仓查询使用"""
        self._session_factory = session_factory

    async def _execute_mappings(self, statement: Any) -> list[dict[str, Any]]:
        """在 ClickHouse 会话中执行查询并把结果行转为字典列表"""
        async with self._session_factory() as session:
            result = await session.execute(statement)
            return [dict(row) for row in result.mappings().all()]

    async def get_api_average_speed_clickhouse_mapper_async(
        self,
    ) -> list[dict[str, Any]]:
        """从 ADS 层查询各接口平均响应时间与调用次数，按平均响应时间降序"""
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
            raise RuntimeError(
                Messages.APILOG_CLICKHOUSE_QUERY_FAILED(error)
            ) from error

    async def get_called_count_clickhouse_mapper_async(
        self,
    ) -> list[dict[str, Any]]:
        """从 ADS 层查询各接口调用次数统计，按调用次数降序"""
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
            raise RuntimeError(
                Messages.APILOG_CLICKHOUSE_QUERY_FAILED(error)
            ) from error


@lru_cache
def get_api_log_mapper(session_factory: ClickHouseSessionFactory) -> ApiLogMapper:
    """获取 API 日志数仓 Mapper 的进程级单例"""
    return ApiLogMapper(session_factory)
