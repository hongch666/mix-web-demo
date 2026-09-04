import asyncio
from datetime import datetime
from functools import lru_cache
from typing import Any

from app.core.constants import Messages, WarehouseScripts
from app.core.db import ClickhouseConnectionPool, get_clickhouse_connection_pool


class UserMapper:
    """用户分析数仓查询 Mapper"""

    def __init__(self) -> None:
        self._clickhouse_pool: ClickhouseConnectionPool = (
            get_clickhouse_connection_pool()
        )

    async def _execute(
        self, query: str, params: dict[str, Any]
    ) -> list[tuple[Any, ...]]:
        # 连接获取与归还均为可能阻塞的池操作，统一走异步包装避免阻塞事件循环
        conn: Any = await self._clickhouse_pool.get_connection_async()
        try:
            return await asyncio.to_thread(conn.execute, query, params)
        finally:
            await self._clickhouse_pool.return_connection_async(conn)

    async def get_new_followers_by_day(
        self, user_id: int, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        rows = await self._execute(
            WarehouseScripts.USER_FOLLOWERS_BY_DAY_QUERY,
            {"user_id": user_id, "start_date": start_date, "end_date": end_date},
        )
        return [{"date": row[0], "count": int(row[1] or 0)} for row in rows]

    async def get_article_view_distribution(self, user_id: int) -> dict[str, Any]:
        rows = await self._execute(
            WarehouseScripts.USER_VIEW_DISTRIBUTION_QUERY, {"user_id": user_id}
        )
        articles = [
            {
                "article_id": int(row[0]),
                "title": str(row[1] or Messages.UNKNOWN_ARTICLE),
                "views": int(row[2] or 0),
            }
            for row in rows
        ]
        return {
            "total_views": sum(item["views"] for item in articles),
            "articles": articles,
        }

    async def get_author_follow_statistics(
        self, user_id: int, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        total_rows, daily_rows = await asyncio.gather(
            self._execute(
                WarehouseScripts.USER_TOTAL_FOLLOWS_QUERY, {"user_id": user_id}
            ),
            self._execute(
                WarehouseScripts.USER_DAILY_FOLLOW_QUERY,
                {"user_id": user_id, "start_date": start_date, "end_date": end_date},
            ),
        )
        return {
            "total_authors": int(total_rows[0][0] or 0) if total_rows else 0,
            "daily_follows": [
                {"date": row[0], "count": int(row[1] or 0)} for row in daily_rows
            ],
        }

    async def get_monthly_action_trend(
        self, user_id: int, metric: str, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        allowed_metrics = {"comment_count", "like_count", "collect_count"}
        if metric not in allowed_metrics:
            raise ValueError(Messages.USER_ANALYSIS_METRIC_UNSUPPORTED(metric))
        query = WarehouseScripts.USER_MONTHLY_ACTION_QUERY.replace("%(metric)s", metric)
        rows = await self._execute(
            query,
            {"user_id": user_id, "start_date": start_date, "end_date": end_date},
        )
        trends = [{"date": row[0], "count": int(row[1] or 0)} for row in rows]
        return {"total": sum(item["count"] for item in trends), "daily_trends": trends}

    async def get_user_profile(self, user_id: int) -> dict[str, Any]:
        """从 ADS 层获取用户画像总览（作为观众与作为作者的累计指标）"""
        rows = await self._execute(
            WarehouseScripts.USER_PROFILE_QUERY, {"user_id": user_id}
        )
        if not rows:
            raise RuntimeError(Messages.CLICKHOUSE_USER_PROFILE_EMPTY)
        row = rows[0]
        return {
            "user_id": int(row[0]),
            "user_name": str(row[1] or ""),
            "total_articles": int(row[2] or 0),
            "total_views_received": int(row[3] or 0),
            "total_likes_received": int(row[4] or 0),
            "total_collects_received": int(row[5] or 0),
            "total_followers": int(row[6] or 0),
            "total_likes_given": int(row[7] or 0),
            "total_collects_given": int(row[8] or 0),
            "total_comments": int(row[9] or 0),
            "total_focus": int(row[10] or 0),
            "last_active_time": row[11],
        }


@lru_cache()
def get_user_mapper() -> UserMapper:
    """获取 UserMapper 单例实例"""
    return UserMapper()
