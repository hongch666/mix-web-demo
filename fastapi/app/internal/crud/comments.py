import asyncio
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List

from app.core.base import Logger
from app.internal.models import Comments, User
from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session

sa_func = func


class CommentsMapper:
    """评论 Mapper"""

    async def _get_ai_comments_num_by_article_id_mapper_sync(
        self, article_id: int, db: Session
    ) -> int:
        # 第一步: 查询所有 role 为 "ai" 的用户ID
        ai_user_statement = select(User.id).where(User.role == "ai")
        ai_user_ids = db.execute(ai_user_statement).scalars().all()

        # 如果没有AI用户,直接返回0
        if not ai_user_ids:
            return 0

        # 第二步: 查询当前文章中,用户ID在AI用户ID数组范围内的评论总数
        comments_statement = select(Comments).where(
            Comments.article_id == article_id, Comments.user_id.in_(ai_user_ids)
        )
        ai_comments = db.execute(comments_statement).scalars().all()

        return len(ai_comments)

    async def _create_comment_mapper_sync(
        self, comment: Comments, db: Session
    ) -> Comments:
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment

    async def _delete_ai_comments_by_article_id_mapper_sync(
        self, article_id: int, db: Session
    ) -> None:
        # 查询所有 role 为 "ai" 的用户ID
        ai_user_statement = select(User.id).where(User.role == "ai")
        ai_user_ids = db.execute(ai_user_statement).scalars().all()
        comments_statement = select(Comments).where(
            Comments.article_id == article_id, Comments.user_id.in_(ai_user_ids)
        )
        comments_to_delete = db.execute(comments_statement).scalars().all()

        for comment in comments_to_delete:
            db.delete(comment)

        db.commit()

    async def _get_monthly_comment_trend_mapper_sync(
        self, db: Session, user_id: int
    ) -> Dict[str, Any]:
        """获取用户本月评论的趋势"""

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
                cast(Comments.create_time, Date).label("date"),
                sa_func.count(Comments.id).label("count"),
            )
            .where(
                Comments.user_id == user_id,
                Comments.create_time >= first_day,
                Comments.create_time < last_day,
            )
            .group_by(cast(Comments.create_time, Date))
            .order_by(cast(Comments.create_time, Date))
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
            f"用户 {user_id} 本月评论趋势: 总数={total}, 天数={len(daily_trends)}"
        )
        return {"total": total, "daily_trends": daily_trends}

    async def get_ai_comments_num_by_article_id_mapper_async(
        self, article_id: int, db: Session
    ) -> int:
        return await self._get_ai_comments_num_by_article_id_mapper_sync(article_id, db)

    async def create_comment_mapper_async(
        self, comment: Comments, db: Session
    ) -> Comments:
        return await self._create_comment_mapper_sync(comment, db)

    async def delete_ai_comments_by_article_id_mapper_async(
        self, article_id: int, db: Session
    ) -> None:
        await asyncio.to_thread(
            self._delete_ai_comments_by_article_id_mapper_sync, article_id, db
        )

    async def get_monthly_comment_trend_mapper_async(
        self, db: Session, user_id: int
    ) -> Dict[str, Any]:
        return await self._get_monthly_comment_trend_mapper_sync(db, user_id)


@lru_cache()
def get_comments_mapper() -> CommentsMapper:
    return CommentsMapper()
