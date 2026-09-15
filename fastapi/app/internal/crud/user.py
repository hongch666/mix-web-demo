import asyncio
from datetime import datetime
from functools import lru_cache
from typing import Any

from sqlalchemy import desc, func, select

from app.core.constants import Messages
from app.core.db import ClickHouseSessionFactory
from app.internal.models import AdsUserDay, AdsUserStats, AdsUserViewArticle, DimUser


def _date_value(value: datetime) -> Any:
    """ClickHouse Date 列不能直接比较带时间的 datetime"""

    return value.date()


class UserMapper:
    """用户分析数仓 Mapper，查询使用 SQLAlchemy ClickHouse ORM"""

    def __init__(self, session_factory: ClickHouseSessionFactory) -> None:
        self._session_factory = session_factory

    async def _execute_mappings(self, statement: Any) -> list[dict[str, Any]]:
        async with self._session_factory() as session:
            result = await session.execute(statement)
            return [dict(row) for row in result.mappings().all()]

    async def get_new_followers_by_day(
        self, user_id: int, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        statement = (
            select(AdsUserDay.stat_date.label("date"), AdsUserDay.focus_count.label("count"))
            .where(
                AdsUserDay.user_id == user_id,
                AdsUserDay.stat_date >= _date_value(start_date),
                AdsUserDay.stat_date < _date_value(end_date),
            )
            .order_by(AdsUserDay.stat_date)
        )
        rows = await self._execute_mappings(statement)
        return [{"date": row.get("date"), "count": int(row.get("count") or 0)} for row in rows]

    async def get_article_view_distribution(self, user_id: int) -> dict[str, Any]:
        statement = (
            select(
                AdsUserViewArticle.article_id,
                AdsUserViewArticle.article_title.label("title"),
                AdsUserViewArticle.view_count.label("views"),
            )
            .where(AdsUserViewArticle.user_id == user_id, AdsUserViewArticle.article_id > 0)
            .order_by(desc(AdsUserViewArticle.view_count))
        )
        rows = await self._execute_mappings(statement)
        articles = [
            {
                "article_id": int(row.get("article_id") or 0),
                "title": str(row.get("title") or Messages.UNKNOWN_ARTICLE),
                "views": int(row.get("views") or 0),
            }
            for row in rows
        ]
        return {"total_views": sum(item["views"] for item in articles), "articles": articles}

    async def get_author_follow_statistics(
        self, user_id: int, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        total_statement = select(AdsUserStats.total_followers.label("total_followers")).where(
            AdsUserStats.user_id == user_id
        )
        daily_statement = (
            select(AdsUserDay.stat_date.label("date"), AdsUserDay.focus_count.label("count"))
            .where(
                AdsUserDay.user_id == user_id,
                AdsUserDay.stat_date >= _date_value(start_date),
                AdsUserDay.stat_date < _date_value(end_date),
            )
            .order_by(AdsUserDay.stat_date)
        )
        total_rows, daily_rows = await asyncio.gather(
            self._execute_mappings(total_statement), self._execute_mappings(daily_statement)
        )
        return {
            "total_authors": int(total_rows[0].get("total_followers") or 0) if total_rows else 0,
            "daily_follows": [
                {"date": row.get("date"), "count": int(row.get("count") or 0)}
                for row in daily_rows
            ],
        }

    async def get_monthly_action_trend(
        self, user_id: int, metric: str, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        metric_columns = {
            "comment_count": AdsUserDay.comment_count,
            "like_count": AdsUserDay.like_count,
            "collect_count": AdsUserDay.collect_count,
        }
        metric_column = metric_columns.get(metric)
        if metric_column is None:
            raise ValueError(Messages.USER_ANALYSIS_METRIC_UNSUPPORTED(metric))
        statement = (
            select(AdsUserDay.stat_date.label("date"), metric_column.label("count"))
            .where(
                AdsUserDay.user_id == user_id,
                AdsUserDay.stat_date >= _date_value(start_date),
                AdsUserDay.stat_date < _date_value(end_date),
            )
            .order_by(AdsUserDay.stat_date)
        )
        rows = await self._execute_mappings(statement)
        trends = [{"date": row.get("date"), "count": int(row.get("count") or 0)} for row in rows]
        return {"total": sum(item["count"] for item in trends), "daily_trends": trends}

    async def get_user_profile(self, user_id: int) -> dict[str, Any]:
        statement = (
            select(
                AdsUserStats.user_id,
                func.ifNull(DimUser.name, "").label("user_name"),
                AdsUserStats.total_articles,
                AdsUserStats.total_views_received,
                AdsUserStats.total_likes_received,
                AdsUserStats.total_collects_received,
                AdsUserStats.total_followers,
                AdsUserStats.total_likes_given,
                AdsUserStats.total_collects_given,
                AdsUserStats.total_comments,
                AdsUserStats.total_focus,
                AdsUserStats.last_active_time,
            )
            .select_from(AdsUserStats)
            .outerjoin(DimUser, AdsUserStats.user_id == DimUser.id)
            .where(AdsUserStats.user_id == user_id)
        )
        rows = await self._execute_mappings(statement)
        if not rows:
            raise RuntimeError(Messages.CLICKHOUSE_USER_PROFILE_EMPTY)
        row = rows[0]
        return {
            "user_id": int(row.get("user_id") or 0),
            "user_name": str(row.get("user_name") or ""),
            "total_articles": int(row.get("total_articles") or 0),
            "total_views_received": int(row.get("total_views_received") or 0),
            "total_likes_received": int(row.get("total_likes_received") or 0),
            "total_collects_received": int(row.get("total_collects_received") or 0),
            "total_followers": int(row.get("total_followers") or 0),
            "total_likes_given": int(row.get("total_likes_given") or 0),
            "total_collects_given": int(row.get("total_collects_given") or 0),
            "total_comments": int(row.get("total_comments") or 0),
            "total_focus": int(row.get("total_focus") or 0),
            "last_active_time": row.get("last_active_time"),
        }


@lru_cache()
def get_user_mapper(session_factory: ClickHouseSessionFactory) -> UserMapper:
    return UserMapper(session_factory)
