import asyncio
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List

from app.core.base import Logger
from app.core.constants import Messages
from app.internal.clients import NestjsClient, SpringClient
from dateutil.relativedelta import relativedelta


class UserService:
    """用户数据分析 Service"""

    def __init__(self) -> None:
        self._nestjs_client: NestjsClient = NestjsClient()
        self._spring_client: SpringClient = SpringClient()

    async def get_new_followers_service(
        self, user_id: int, period: str = "day"
    ) -> Dict[str, Any]:
        """
        获取新增粉丝数统计
        period: "day" 前7天, "month" 前6个月, "year" 前3年
        """
        try:
            timeline: List[Dict[str, Any]] = []

            if period == "day":
                # 7个独立时间窗口查询改为 asyncio.gather 并行
                async def _one_day(days_ago: int) -> Dict[str, Any]:
                    date: datetime = datetime.now() - timedelta(days=days_ago)
                    start_date: datetime = date.replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    end_date: datetime = date.replace(
                        hour=23, minute=59, second=59, microsecond=999999
                    )
                    count: int = await self._spring_client.get_followers_in_period(
                        user_id, start_date.isoformat(), end_date.isoformat()
                    )
                    return {"date": date.strftime("%Y-%m-%d"), "count": count}

                timeline = await asyncio.gather(
                    *[_one_day(i) for i in range(6, -1, -1)]
                )
            elif period == "month":
                # 6个独立月份窗口查询改为 asyncio.gather 并行
                async def _one_month(months_ago: int) -> Dict[str, Any]:
                    date = datetime.now() - relativedelta(months=months_ago)
                    start_date = date.replace(
                        day=1, hour=0, minute=0, second=0, microsecond=0
                    )
                    end_date = (date.replace(day=1) + relativedelta(months=1)).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    ) - timedelta(seconds=1)
                    count: int = await self._spring_client.get_followers_in_period(
                        user_id, start_date.isoformat(), end_date.isoformat()
                    )
                    return {"month": date.strftime("%Y-%m"), "count": count}

                timeline = await asyncio.gather(
                    *[_one_month(i) for i in range(5, -1, -1)]
                )
            elif period == "year":
                # 3个独立年份窗口查询改为 asyncio.gather 并行
                async def _one_year(years_ago: int) -> Dict[str, Any]:
                    date = datetime.now() - relativedelta(years=years_ago)
                    start_date = date.replace(
                        month=1, day=1, hour=0, minute=0, second=0, microsecond=0
                    )
                    end_date = date.replace(
                        month=12,
                        day=31,
                        hour=23,
                        minute=59,
                        second=59,
                        microsecond=999999,
                    )
                    count: int = await self._spring_client.get_followers_in_period(
                        user_id, start_date.isoformat(), end_date.isoformat()
                    )
                    return {"year": date.strftime("%Y"), "count": count}

                timeline = await asyncio.gather(
                    *[_one_year(i) for i in range(2, -1, -1)]
                )

            return {"period": period, "timeline": timeline}
        except Exception as e:
            Logger.error(Messages.USER_NEW_FOLLOWER_COUNT_FAILED(e))
            return {"period": period, "timeline": []}

    async def get_article_view_distribution_service(
        self, user_id: int
    ) -> Dict[str, Any]:
        """获取用户的文章浏览分布"""
        try:
            return await self._nestjs_client.get_article_view_distribution(user_id)
        except Exception as e:
            Logger.error(Messages.ARTICLE_VIEW_DISTRIBUTION_FAILED(e), exc_info=True)
            return {"total_views": 0, "articles": []}

    async def get_author_follow_statistics_service(
        self, user_id: int
    ) -> Dict[str, Any]:
        """获取用户关注作者的统计"""
        try:
            # 总数查询与7天循环查询相互独立，gather 并行降低延迟
            async def _one_day_follow(days_ago: int) -> Dict[str, Any]:
                date = datetime.now() - timedelta(days=days_ago)
                start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = date.replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )
                result = await self._spring_client.get_daily_follows(
                    user_id, start_date.isoformat(), end_date.isoformat()
                )
                daily_follows_list = result.get("daily_follows", [])
                count = (
                    daily_follows_list[0].get("count", 0) if daily_follows_list else 0
                )
                return {"date": date.strftime("%Y-%m-%d"), "count": count}

            async def _total_follows() -> int:
                return await self._spring_client.get_total_follows(user_id)

            total_authors, *daily_follows = await asyncio.gather(
                _total_follows(),
                *[_one_day_follow(i) for i in range(6, -1, -1)],
            )

            return {"total_authors": total_authors, "daily_follows": daily_follows}
        except Exception as e:
            Logger.error(Messages.USER_AUTHOR_FOLLOW_STATS_FAILED(e))
            return {"total_authors": 0, "daily_follows": []}

    async def get_monthly_comment_trend_service(
        self, user_id: int
    ) -> Dict[str, Any]:
        """获取用户本月评论的趋势"""
        try:
            return await self._spring_client.get_monthly_comment_trend(user_id)
        except Exception as e:
            Logger.error(Messages.USER_COMMENT_TREND_FAILED(e))
            return {"total": 0, "daily_trends": []}

    async def get_monthly_like_trend_service(
        self, user_id: int
    ) -> Dict[str, Any]:
        """获取用户本月点赞的趋势"""
        try:
            return await self._spring_client.get_monthly_like_trend(user_id)
        except Exception as e:
            Logger.error(Messages.USER_LIKE_TREND_FAILED(e))
            return {"total": 0, "daily_trends": []}

    async def get_monthly_collect_trend_service(
        self, user_id: int
    ) -> Dict[str, Any]:
        """获取用户本月收藏的趋势"""
        try:
            return await self._spring_client.get_monthly_collect_trend(user_id)
        except Exception as e:
            Logger.error(Messages.USER_COLLECT_TREND_FAILED(e))
            return {"total": 0, "daily_trends": []}


@lru_cache()
def get_user_service() -> UserService:
    """获取 UserService 单例实例"""
    return UserService()
