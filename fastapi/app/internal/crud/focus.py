import asyncio
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List

from app.core.base import Logger
from app.internal.models import Focus
from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session


class FocusMapper:
    """关注 Mapper"""

    async def _get_total_followers_mapper_sync(self, db: Session, user_id: int) -> int:
        """获取用户的粉丝总数（被多少人关注）"""

        statement = select(func.count(Focus.id)).where(Focus.focus_id == user_id)
        return db.execute(statement).scalar_one()

    async def _get_followers_in_period_mapper_sync(
        self, db: Session, user_id: int, start_date: datetime, end_date: datetime
    ) -> int:
        """获取指定时间段内的新增粉丝数"""

        statement = select(func.count(Focus.id)).where(
            Focus.focus_id == user_id,
            Focus.created_time >= start_date,
            Focus.created_time <= end_date,
        )
        return db.execute(statement).scalar_one()

    async def _get_daily_followers_mapper_sync(
        self, db: Session, user_id: int, start_date: datetime, end_date: datetime
    ) -> List[Any]:
        """获取指定时间段内每天的新增粉丝数"""

        statement = (
            select(
                cast(Focus.created_time, Date).label("date"),
                func.count(Focus.id).label("count"),
            )
            .where(
                Focus.focus_id == user_id,
                Focus.created_time >= start_date,
                Focus.created_time <= end_date,
            )
            .group_by(cast(Focus.created_time, Date))
            .order_by(cast(Focus.created_time, Date))
        )

        results = db.execute(statement).all()
        return results if results else []

    async def _get_total_follows_mapper_sync(self, db: Session, user_id: int) -> int:
        """获取用户的总关注数"""

        statement = select(func.count(Focus.id)).where(Focus.user_id == user_id)
        return db.execute(statement).scalar_one()

    async def _get_daily_follows_mapper_sync(
        self, db: Session, user_id: int, start_date: datetime, end_date: datetime
    ) -> List[Any]:
        """获取指定时间段内每天的关注数"""

        statement = (
            select(
                cast(Focus.created_time, Date).label("date"),
                func.count(Focus.id).label("count"),
            )
            .where(
                Focus.user_id == user_id,
                Focus.created_time >= start_date,
                Focus.created_time <= end_date,
            )
            .group_by(cast(Focus.created_time, Date))
            .order_by(cast(Focus.created_time, Date))
        )

        results = db.execute(statement).all()
        return results if results else []

    async def _get_monthly_follow_trend_mapper_sync(
        self, db: Session, user_id: int
    ) -> Dict[str, Any]:
        """获取用户本月关注的趋势"""

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
                cast(Focus.created_time, Date).label("date"),
                func.count(Focus.id).label("count"),
            )
            .where(
                Focus.user_id == user_id,
                Focus.created_time >= first_day,
                Focus.created_time < last_day,
            )
            .group_by(cast(Focus.created_time, Date))
            .order_by(cast(Focus.created_time, Date))
        )

        results = db.execute(statement).all()

        daily_trends: List[Dict[str, Any]] = []
        total: int = 0
        for row in results:
            date_str = str(row[0])
            count = row[1]
            daily_trends.append({"date": date_str, "count": count})
            total += count

        Logger.debug(
            f"用户 {user_id} 本月关注趋势: 总数={total}, 天数={len(daily_trends)}"
        )
        return {"total": total, "daily_trends": daily_trends}

    async def _get_monthly_follower_trend_mapper_sync(
        self, db: Session, user_id: int
    ) -> Dict[str, Any]:
        """获取用户本月新增粉丝的趋势"""

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
                cast(Focus.created_time, Date).label("date"),
                func.count(Focus.id).label("count"),
            )
            .where(
                Focus.focus_id == user_id,
                Focus.created_time >= first_day,
                Focus.created_time < last_day,
            )
            .group_by(cast(Focus.created_time, Date))
            .order_by(cast(Focus.created_time, Date))
        )

        results = db.execute(statement).all()

        daily_trends: List[Dict[str, Any]] = []
        total: int = 0
        for row in results:
            date_str = str(row[0])
            count = row[1]
            daily_trends.append({"date": date_str, "count": count})
            total += count

        Logger.debug(
            f"用户 {user_id} 本月粉丝趋势: 总数={total}, 天数={len(daily_trends)}"
        )
        return {"total": total, "daily_trends": daily_trends}

    async def get_total_followers_mapper_async(self, db: Session, user_id: int) -> int:
        return await self._get_total_followers_mapper_sync(db, user_id)

    async def get_followers_in_period_mapper_async(
        self, db: Session, user_id: int, start_date: datetime, end_date: datetime
    ) -> int:
        return await asyncio.to_thread(
            self._get_followers_in_period_mapper_sync, db, user_id, start_date, end_date
        )

    async def get_daily_followers_mapper_async(
        self, db: Session, user_id: int, start_date: datetime, end_date: datetime
    ) -> List[Any]:
        return await asyncio.to_thread(
            self._get_daily_followers_mapper_sync, db, user_id, start_date, end_date
        )

    async def get_total_follows_mapper_async(self, db: Session, user_id: int) -> int:
        return await self._get_total_follows_mapper_sync(db, user_id)

    async def get_daily_follows_mapper_async(
        self, db: Session, user_id: int, start_date: datetime, end_date: datetime
    ) -> List[Any]:
        return await asyncio.to_thread(
            self._get_daily_follows_mapper_sync, db, user_id, start_date, end_date
        )

    async def get_monthly_follow_trend_mapper_async(
        self, db: Session, user_id: int
    ) -> Dict[str, Any]:
        return await self._get_monthly_follow_trend_mapper_sync(db, user_id)

    async def get_monthly_follower_trend_mapper_async(
        self, db: Session, user_id: int
    ) -> Dict[str, Any]:
        return await asyncio.to_thread(
            self._get_monthly_follower_trend_mapper_sync, db, user_id
        )


@lru_cache()
def get_focus_mapper() -> FocusMapper:
    """获取 FocusMapper 单例实例"""
    return FocusMapper()
