import asyncio
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional

from app.core.base import Logger
from app.core.db import AsyncSessionLocal
from app.internal.crud import (
    ArticleLogMapper,
    ArticleMapper,
    CollectMapper,
    CommentsMapper,
    FocusMapper,
    LikeMapper,
    get_article_mapper,
    get_articlelog_mapper,
    get_collect_mapper,
    get_comments_mapper,
    get_focus_mapper,
    get_like_mapper,
)
from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Depends


class UserService:
    """用户数据分析 Service"""

    def __init__(
        self,
        focusMapper: Optional[FocusMapper] = None,
        likeMapper: Optional[LikeMapper] = None,
        collectMapper: Optional[CollectMapper] = None,
        articleMapper: Optional[ArticleMapper] = None,
        commentsMapper: Optional[CommentsMapper] = None,
        articleLogMapper: Optional[ArticleLogMapper] = None,
    ) -> None:
        self.focusMapper: Optional[FocusMapper] = focusMapper
        self.likeMapper: Optional[LikeMapper] = likeMapper
        self.collectMapper: Optional[CollectMapper] = collectMapper
        self.articleMapper: Optional[ArticleMapper] = articleMapper
        self.commentsMapper: Optional[CommentsMapper] = commentsMapper
        self.articleLogMapper: Optional[ArticleLogMapper] = articleLogMapper

    async def get_new_followers_service(
        self, db: AsyncSession, user_id: int, period: str = "day"
    ) -> Dict[str, Any]:
        """
        获取新增粉丝数统计
        period: "day" 前7天, "month" 前6个月, "year" 前3年
        """
        try:
            timeline: List[Dict[str, Any]] = []

            if period == "day":
                # 7个独立时间窗口查询改为 asyncio.gather 并行
                # 每个协程使用独立的 AsyncSession，避免同一个 session 并发操作
                async def _one_day(days_ago: int) -> Dict[str, Any]:
                    date: datetime = datetime.now() - timedelta(days=days_ago)
                    start_date: datetime = date.replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    end_date: datetime = date.replace(
                        hour=23, minute=59, second=59, microsecond=999999
                    )
                    async with AsyncSessionLocal() as session:
                        count: int = await self.focusMapper.get_followers_in_period_mapper_async(
                            session, user_id, start_date, end_date
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
                    async with AsyncSessionLocal() as session:
                        count: int = await self.focusMapper.get_followers_in_period_mapper_async(
                            session, user_id, start_date, end_date
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
                    async with AsyncSessionLocal() as session:
                        count: int = await self.focusMapper.get_followers_in_period_mapper_async(
                            session, user_id, start_date, end_date
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
            return await self.articleLogMapper.get_user_view_distribution_mapper(
                user_id
            )
        except Exception as e:
            Logger.error(Messages.ARTICLE_VIEW_DISTRIBUTION_FAILED(e), exc_info=True)
            return {"total_views": 0, "articles": []}

    async def get_author_follow_statistics_service(
        self, db: AsyncSession, user_id: int
    ) -> Dict[str, Any]:
        """获取用户关注作者的统计"""
        try:
            # 总数查询与7天循环查询相互独立，gather 并行降低延迟
            # 每个协程使用独立的 AsyncSession，避免同一个 session 并发操作
            async def _one_day_follow(days_ago: int) -> Dict[str, Any]:
                date = datetime.now() - timedelta(days=days_ago)
                start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = date.replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )
                count = 0
                async with AsyncSessionLocal() as session:
                    results = await self.focusMapper.get_daily_follows_mapper_async(
                        session, user_id, start_date, end_date
                    )
                if results and len(results) > 0:
                    count = results[0][1]
                return {"date": date.strftime("%Y-%m-%d"), "count": count}

            async def _total_follows() -> int:
                async with AsyncSessionLocal() as session:
                    return await self.focusMapper.get_total_follows_mapper_async(
                        session, user_id
                    )

            total_authors, *daily_follows = await asyncio.gather(
                _total_follows(),
                *[_one_day_follow(i) for i in range(6, -1, -1)],
            )

            return {"total_authors": total_authors, "daily_follows": daily_follows}
        except Exception as e:
            Logger.error(Messages.USER_AUTHOR_FOLLOW_STATS_FAILED(e))
            return {"total_authors": 0, "daily_follows": []}

    async def get_monthly_comment_trend_service(
        self, db: AsyncSession, user_id: int
    ) -> Dict[str, Any]:
        """获取用户本月评论的趋势"""
        try:
            return await self.commentsMapper.get_monthly_comment_trend_mapper_async(
                db, user_id
            )
        except Exception as e:
            Logger.error(Messages.USER_COMMENT_TREND_FAILED(e))
            return {"total": 0, "daily_trends": []}

    async def get_monthly_like_trend_service(
        self, db: AsyncSession, user_id: int
    ) -> Dict[str, Any]:
        """获取用户本月点赞的趋势"""
        try:
            return await self.likeMapper.get_monthly_like_trend_mapper_async(
                db, user_id
            )
        except Exception as e:
            Logger.error(Messages.USER_LIKE_TREND_FAILED(e))
            return {"total": 0, "daily_trends": []}

    async def get_monthly_collect_trend_service(
        self, db: AsyncSession, user_id: int
    ) -> Dict[str, Any]:
        """获取用户本月收藏的趋势"""
        try:
            return await self.collectMapper.get_monthly_collect_trend_mapper_async(
                db, user_id
            )
        except Exception as e:
            Logger.error(Messages.USER_COLLECT_TREND_FAILED(e))
            return {"total": 0, "daily_trends": []}


@lru_cache()
def get_user_service(
    focusMapper: FocusMapper = Depends(get_focus_mapper),
    likeMapper: LikeMapper = Depends(get_like_mapper),
    collectMapper: CollectMapper = Depends(get_collect_mapper),
    articleMapper: ArticleMapper = Depends(get_article_mapper),
    commentsMapper: CommentsMapper = Depends(get_comments_mapper),
    articleLogMapper: ArticleLogMapper = Depends(get_articlelog_mapper),
) -> UserService:
    """获取 UserService 单例实例"""
    return UserService(
        focusMapper,
        likeMapper,
        collectMapper,
        articleMapper,
        commentsMapper,
        articleLogMapper,
    )
