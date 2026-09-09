import asyncio
from functools import lru_cache
from typing import Any

from sqlalchemy import desc, select

from app.core.constants import Messages
from app.core.db import (
    ClickHouseAsyncSessionLocal,
    ClickhouseConnectionPool,
    get_clickhouse_connection_pool,
)
from app.internal.models import (
    AdsCategoryStats,
    AdsMonthlyPublish,
    AdsPlatformStats,
    AdsSearchKeyword,
    AdsTop10Article,
)


class ArticleMapper:
    """文章数仓 Mapper，查询使用 SQLAlchemy ClickHouse ORM。"""

    def __init__(self) -> None:
        # 这两个方法仍供现有缓存版本检查使用，该缓存依赖 clickhouse-driver 连接。
        self._clickhouse_pool: ClickhouseConnectionPool = (
            get_clickhouse_connection_pool()
        )

    async def _execute_mappings(self, statement: Any) -> list[dict[str, Any]]:
        async with ClickHouseAsyncSessionLocal() as session:
            result = await session.execute(statement)
            return [dict(row) for row in result.mappings().all()]

    async def get_top10_articles_clickhouse_mapper_async(self) -> list[dict[str, Any]]:
        columns = (
            AdsTop10Article.id,
            AdsTop10Article.title,
            AdsTop10Article.tags,
            AdsTop10Article.status,
            AdsTop10Article.views,
            AdsTop10Article.create_at,
            AdsTop10Article.update_at,
            AdsTop10Article.user_id,
            AdsTop10Article.sub_category_id,
        )
        statement = select(*columns).order_by(desc(AdsTop10Article.views)).limit(10)
        return await self._execute_mappings(statement)

    async def get_search_keywords_clickhouse_mapper_async(self) -> list[str]:
        statement = select(AdsSearchKeyword.keyword).order_by(AdsSearchKeyword.keyword)
        rows = await self._execute_mappings(statement)
        return [str(row["keyword"]) for row in rows if row.get("keyword")]

    async def get_category_article_count_clickhouse_mapper_async(
        self,
    ) -> list[dict[str, Any]]:
        statement = select(
            AdsCategoryStats.parent_category_id.label("category_id"),
            AdsCategoryStats.category_name,
            AdsCategoryStats.article_count,
        ).order_by(desc(AdsCategoryStats.article_count))
        rows = await self._execute_mappings(statement)
        return [
            {
                "category_id": row.get("category_id"),
                "category_name": str(row.get("category_name") or ""),
                "article_count": int(row.get("article_count") or 0),
            }
            for row in rows
        ]

    async def get_monthly_publish_count_clickhouse_mapper_async(
        self,
    ) -> list[dict[str, Any]]:
        statement = select(
            AdsMonthlyPublish.year_month,
            AdsMonthlyPublish.article_count.label("count"),
        ).order_by(AdsMonthlyPublish.year_month)
        rows = await self._execute_mappings(statement)
        return [
            {
                "year_month": str(row.get("year_month") or ""),
                "count": int(row.get("count") or 0),
            }
            for row in rows
        ]

    async def get_platform_stats_clickhouse_mapper_async(self) -> dict[str, Any]:
        statement = (
            select(
                AdsPlatformStats.total_views,
                AdsPlatformStats.total_articles,
                AdsPlatformStats.active_authors,
                AdsPlatformStats.average_views,
                AdsPlatformStats.total_likes,
                AdsPlatformStats.average_likes,
                AdsPlatformStats.total_collects,
                AdsPlatformStats.average_collects,
            )
            .order_by(desc(AdsPlatformStats.stat_time))
            .limit(1)
        )
        rows = await self._execute_mappings(statement)
        if not rows:
            raise RuntimeError(Messages.CLICKHOUSE_PLATFORM_STATS_EMPTY)
        row = rows[0]
        return {
            "total_views": int(row.get("total_views") or 0),
            "total_articles": int(row.get("total_articles") or 0),
            "active_authors": int(row.get("active_authors") or 0),
            "average_views": float(row.get("average_views") or 0),
            "total_likes": int(row.get("total_likes") or 0),
            "average_likes": float(row.get("average_likes") or 0),
            "total_collects": int(row.get("total_collects") or 0),
            "average_collects": float(row.get("average_collects") or 0),
        }

    async def get_clickhouse_connection_async(self) -> Any:
        """兼容旧缓存实现：获取 clickhouse-driver 连接。"""

        return await asyncio.to_thread(self._clickhouse_pool.get_connection)

    async def return_clickhouse_connection_async(self, conn: Any) -> None:
        """兼容旧缓存实现：归还 clickhouse-driver 连接。"""

        await asyncio.to_thread(self._clickhouse_pool.return_connection, conn)


@lru_cache()
def get_article_mapper() -> ArticleMapper:
    return ArticleMapper()
