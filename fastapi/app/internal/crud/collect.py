from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List

from app.core.base import Logger
from app.core.constants import Messages
from app.internal.models import Collect
from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from . import get_article_mapper


class CollectMapper:
    """收藏 Mapper"""

    async def _get_total_collects_mapper_sync(self, db: AsyncSession) -> int:
        """获取所有文章的总收藏数"""

        statement = select(func.count(Collect.id))
        return (await db.execute(statement)).scalar_one()

    async def _get_average_collects_mapper_sync(self, db: AsyncSession) -> float:
        """获取每篇文章的平均收藏数"""

        article_mapper = get_article_mapper()
        total_articles = await article_mapper._get_total_articles_mapper_sync(db)
        if total_articles == 0:
            return 0
        total_collects = await self._get_total_collects_mapper_sync(db)
        return round(total_collects / total_articles, 2)

    async def _get_monthly_collect_trend_mapper_sync(
        self, db: AsyncSession, user_id: int
    ) -> Dict[str, Any]:
        """获取用户本月收藏的趋势"""

        today = datetime.now()
        first_day = datetime(today.year, today.month, 1)
        if today.month == 12:
            last_day = datetime(today.year + 1, 1, 1).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        else:
            last_day = datetime(today.year, today.month + 1, 1).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        statement = (
            select(
                cast(Collect.created_time, Date).label("date"),
                func.count(Collect.id).label("count"),
            )
            .where(
                Collect.user_id == user_id,
                Collect.created_time >= first_day,
                Collect.created_time < last_day,
            )
            .group_by(cast(Collect.created_time, Date))
            .order_by(cast(Collect.created_time, Date))
        )

        results = (await db.execute(statement)).all()

        daily_trends: List[Dict[str, Any]] = []
        total: int = 0
        for row in results:
            date_str = str(row[0])
            count = row[1]
            daily_trends.append({"date": date_str, "count": count})
            total += count

        Logger.debug(
            Messages.USER_MONTHLY_TREND(user_id, "收藏", total, len(daily_trends))
        )
        return {"total": total, "daily_trends": daily_trends}

    async def get_total_collects_mapper_async(self, db: AsyncSession) -> int:
        return await self._get_total_collects_mapper_sync(db)

    async def get_average_collects_mapper_async(self, db: AsyncSession) -> float:
        return await self._get_average_collects_mapper_sync(db)

    async def get_monthly_collect_trend_mapper_async(
        self, db: AsyncSession, user_id: int
    ) -> Dict[str, Any]:
        return await self._get_monthly_collect_trend_mapper_sync(db, user_id)


@lru_cache()
def get_collect_mapper() -> CollectMapper:
    """获取 CollectMapper 单例实例"""
    return CollectMapper()
