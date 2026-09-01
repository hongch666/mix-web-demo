import asyncio
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any

from dateutil.relativedelta import relativedelta

from app.core.base import Logger
from app.core.constants import Messages
from app.internal.clients import NestjsClient, SpringClient
from app.internal.crud import UserAnalysisMapper


class UserService:
    """用户数据分析 Service"""

    def __init__(self) -> None:
        self._nestjs_client: NestjsClient = NestjsClient()
        self._spring_client: SpringClient = SpringClient()
        self._user_analysis_mapper: UserAnalysisMapper = UserAnalysisMapper()

    @staticmethod
    def _period_dates(period: str) -> tuple[datetime, datetime, int, str]:
        now = datetime.now()
        if period == "day":
            start = (now - timedelta(days=6)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            return start, now + timedelta(days=1), 7, "date"
        if period == "month":
            start = (now - relativedelta(months=5)).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            return start, now + relativedelta(months=1), 6, "month"
        start = now.replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        ) - relativedelta(years=2)
        return (
            start,
            now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            + relativedelta(years=1),
            3,
            "year",
        )

    @staticmethod
    def _build_period_timeline(
        period: str, start: datetime, count: int, rows: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        values = {str(row["date"]): int(row["count"]) for row in rows}
        timeline: list[dict[str, Any]] = []
        for index in range(count - 1, -1, -1):
            if period == "day":
                date = start + timedelta(days=index)
                key = date.strftime("%Y-%m-%d")
                timeline.append({"date": key, "count": values.get(key, 0)})
            elif period == "month":
                date = start + relativedelta(months=index)
                key = date.strftime("%Y-%m")
                timeline.append({"month": key, "count": values.get(key, 0)})
            else:
                date = start + relativedelta(years=index)
                key = date.strftime("%Y")
                timeline.append({"year": key, "count": values.get(key, 0)})
        return timeline

    async def get_new_followers_service(
        self, user_id: int, period: str = "day"
    ) -> dict[str, Any]:
        """
        获取新增粉丝数统计
        period: "day" 前7天, "month" 前6个月, "year" 前3年
        """
        try:
            start, end, count, _ = self._period_dates(period)
            rows = await self._user_analysis_mapper.get_new_followers_by_day(
                user_id, start, end
            )
            if period != "day":
                for row in rows:
                    value = row["date"]
                    row["date"] = value.strftime("%Y-%m" if period == "month" else "%Y")
                grouped: dict[str, int] = {}
                for row in rows:
                    grouped[str(row["date"])] = grouped.get(str(row["date"]), 0) + int(
                        row["count"]
                    )
                rows = [{"date": key, "count": value} for key, value in grouped.items()]
            return {
                "period": period,
                "timeline": self._build_period_timeline(period, start, count, rows),
            }
        except Exception as ch_error:
            Logger.warning(
                Messages.SERVICE_CLICKHOUSE_DEGRADE_TO_DB(
                    "get_new_followers_service", ch_error
                )
            )
        try:
            timeline: list[dict[str, Any]] = []

            if period == "day":
                # 7个独立时间窗口查询改为 asyncio.gather 并行
                async def _one_day(days_ago: int) -> dict[str, Any]:
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
                async def _one_month(months_ago: int) -> dict[str, Any]:
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
                async def _one_year(years_ago: int) -> dict[str, Any]:
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
    ) -> dict[str, Any]:
        """获取用户的文章浏览分布"""
        try:
            return await self._user_analysis_mapper.get_article_view_distribution(
                user_id
            )
        except Exception as ch_error:
            Logger.warning(
                Messages.SERVICE_CLICKHOUSE_DEGRADE_TO_DB(
                    "get_article_view_distribution_service", ch_error
                )
            )
        try:
            return await self._nestjs_client.get_article_view_distribution(user_id)
        except Exception as e:
            Logger.error(Messages.ARTICLE_VIEW_DISTRIBUTION_FAILED(e), exc_info=True)
            return {"total_views": 0, "articles": []}

    async def get_author_follow_statistics_service(
        self, user_id: int
    ) -> dict[str, Any]:
        """获取用户关注作者的统计"""
        try:
            now = datetime.now()
            start = (now - timedelta(days=6)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end = now + timedelta(days=1)
            return await self._user_analysis_mapper.get_author_follow_statistics(
                user_id, start, end
            )
        except Exception as ch_error:
            Logger.warning(
                Messages.SERVICE_CLICKHOUSE_DEGRADE_TO_DB(
                    "get_author_follow_statistics_service", ch_error
                )
            )
        try:
            # 总数查询与7天循环查询相互独立，gather 并行降低延迟
            async def _one_day_follow(days_ago: int) -> dict[str, Any]:
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

    async def get_monthly_comment_trend_service(self, user_id: int) -> dict[str, Any]:
        """获取用户本月评论的趋势"""
        try:
            return await self._user_analysis_mapper.get_monthly_action_trend(
                user_id,
                "comment_count",
                datetime.now().replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                ),
                datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                + relativedelta(months=1),
            )
        except Exception as ch_error:
            Logger.warning(
                Messages.SERVICE_CLICKHOUSE_DEGRADE_TO_DB(
                    "get_monthly_comment_trend_service", ch_error
                )
            )
        try:
            return await self._spring_client.get_monthly_comment_trend(user_id)
        except Exception as e:
            Logger.error(Messages.USER_COMMENT_TREND_FAILED(e))
            return {"total": 0, "daily_trends": []}

    async def get_monthly_like_trend_service(self, user_id: int) -> dict[str, Any]:
        """获取用户本月点赞的趋势"""
        try:
            start = datetime.now().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            return await self._user_analysis_mapper.get_monthly_action_trend(
                user_id, "like_count", start, start + relativedelta(months=1)
            )
        except Exception as ch_error:
            Logger.warning(
                Messages.SERVICE_CLICKHOUSE_DEGRADE_TO_DB(
                    "get_monthly_like_trend_service", ch_error
                )
            )
        try:
            return await self._spring_client.get_monthly_like_trend(user_id)
        except Exception as e:
            Logger.error(Messages.USER_LIKE_TREND_FAILED(e))
            return {"total": 0, "daily_trends": []}

    async def get_monthly_collect_trend_service(self, user_id: int) -> dict[str, Any]:
        """获取用户本月收藏的趋势"""
        try:
            start = datetime.now().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            return await self._user_analysis_mapper.get_monthly_action_trend(
                user_id, "collect_count", start, start + relativedelta(months=1)
            )
        except Exception as ch_error:
            Logger.warning(
                Messages.SERVICE_CLICKHOUSE_DEGRADE_TO_DB(
                    "get_monthly_collect_trend_service", ch_error
                )
            )
        try:
            return await self._spring_client.get_monthly_collect_trend(user_id)
        except Exception as e:
            Logger.error(Messages.USER_COLLECT_TREND_FAILED(e))
            return {"total": 0, "daily_trends": []}

    async def get_user_profile_service(self, user_id: int) -> dict[str, Any]:
        """获取用户画像总览（优先 ClickHouse ADS，降级为远程组装）"""
        try:
            return await self._user_analysis_mapper.get_user_profile(user_id)
        except Exception as ch_error:
            Logger.warning(
                Messages.SERVICE_CLICKHOUSE_DEGRADE_TO_DB(
                    "get_user_profile_service", ch_error
                )
            )
        # 降级：并行调用 Spring 远程接口组装画像数据
        (
            total_articles,
            total_views_received,
            total_likes_received,
            total_collects_received,
            total_followers,
        ) = await asyncio.gather(
            self._spring_client.get_user_article_count(user_id),
            self._spring_client.get_user_total_views(user_id),
            self._spring_client.get_user_total_likes(user_id),
            self._spring_client.get_user_total_collects(user_id),
            self._spring_client.get_user_total_followers(user_id),
        )
        return {
            "user_id": user_id,
            "user_name": "",
            "total_articles": int(total_articles or 0),
            "total_views_received": int(total_views_received or 0),
            "total_likes_received": int(total_likes_received or 0),
            "total_collects_received": int(total_collects_received or 0),
            "total_followers": int(total_followers or 0),
            "total_likes_given": 0,
            "total_collects_given": 0,
            "total_comments": 0,
            "total_focus": 0,
            "last_active_time": None,
        }


@lru_cache()
def get_user_service() -> UserService:
    """获取 UserService 单例实例"""
    return UserService()
