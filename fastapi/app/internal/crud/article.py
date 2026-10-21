from functools import lru_cache
from typing import Any

from sqlalchemy import desc, select

from app.core.constants import Messages
from app.core.db import ClickHouseSessionFactory
from app.internal.models import (
    AdsCategoryStats,
    AdsMonthlyPublish,
    AdsPlatformStats,
    AdsSearchKeyword,
    AdsTop10Article,
)


class ArticleMapper:
    """文章数仓 Mapper，查询使用 SQLAlchemy ClickHouse ORM"""

    def __init__(self, session_factory: ClickHouseSessionFactory) -> None:
        """保存 ClickHouse 会话工厂供各数仓查询使用"""
        self._session_factory = session_factory

    async def _execute_mappings(self, statement: Any) -> list[dict[str, Any]]:
        """在 ClickHouse 会话中执行查询并把结果行转为字典列表"""
        async with self._session_factory() as session:
            result = await session.execute(statement)
            return [dict(row) for row in result.mappings().all()]

    async def get_top10_articles_clickhouse_mapper_async(self) -> list[dict[str, Any]]:
        """查询阅读量最高的 10 篇文章明细，包含作者名与子分类信息"""
        columns = (
            AdsTop10Article.id,
            AdsTop10Article.title,
            AdsTop10Article.tags,
            AdsTop10Article.status,
            AdsTop10Article.views,
            AdsTop10Article.create_at,
            AdsTop10Article.update_at,
            AdsTop10Article.user_id,
            # 数仓 ADS 层已带作者名，对外统一按 username 字段返回
            AdsTop10Article.user_name.label("username"),
            AdsTop10Article.sub_category_id,
        )
        statement = select(*columns).order_by(desc(AdsTop10Article.views)).limit(10)
        return await self._execute_mappings(statement)

    async def get_search_keywords_clickhouse_mapper_async(self) -> list[str]:
        """查询全部搜索关键词，过滤空值后返回字符串列表"""
        statement = select(AdsSearchKeyword.keyword).order_by(AdsSearchKeyword.keyword)
        rows = await self._execute_mappings(statement)
        return [str(row["keyword"]) for row in rows if row.get("keyword")]

    async def get_category_article_count_clickhouse_mapper_async(
        self,
    ) -> list[dict[str, Any]]:
        """查询各一级分类的文章数量，按数量降序返回"""
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
        """查询按月统计的文章发布数量，按月份升序返回"""
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
        """查询平台整体统计快照（阅读、文章、点赞、收藏等汇总指标），取最新一条"""
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


@lru_cache
def get_article_mapper(session_factory: ClickHouseSessionFactory) -> ArticleMapper:
    """获取文章数仓 Mapper 的进程级单例"""
    return ArticleMapper(session_factory)
