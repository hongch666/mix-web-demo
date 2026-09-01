from functools import lru_cache
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.internal.models import AiHistory


class AiHistoryMapper:
    """AI 历史记录 Mapper"""

    async def create_ai_history_async(
        self, ai_history: AiHistory, db: AsyncSession
    ) -> AiHistory:
        db.add(ai_history)
        await db.commit()
        await db.refresh(ai_history)
        return ai_history

    async def get_all_ai_history_by_userid_async(
        self, db: AsyncSession, user_id: int, limit: Optional[int]
    ) -> list[AiHistory]:
        if limit is None:
            statement = (
                select(AiHistory)
                .where(AiHistory.user_id == user_id)
                .order_by(AiHistory.created_at.asc())
            )
        else:
            statement = (
                select(AiHistory)
                .where(AiHistory.user_id == user_id)
                .order_by(AiHistory.created_at.asc())
                .limit(limit)
            )
        return (await db.execute(statement)).scalars().all()

    async def delete_ai_history_by_userid_async(
        self, db: AsyncSession, user_id: int
    ) -> None:
        statement = select(AiHistory).where(AiHistory.user_id == user_id)
        histories = (await db.execute(statement)).scalars().all()
        for history in histories:
            await db.delete(history)
        await db.commit()

    async def get_ai_history_by_id_async(
        self, db: AsyncSession, id: int
    ) -> Optional[AiHistory]:
        """根据ID查询AI历史记录"""
        statement = select(AiHistory).where(AiHistory.id == id)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def update_ai_history_async(
        self, db: AsyncSession, ai_history: AiHistory
    ) -> AiHistory:
        """更新AI历史记录"""
        merged = await db.merge(ai_history)
        await db.commit()
        await db.refresh(merged)
        return merged

    async def delete_ai_history_by_id_async(self, db: AsyncSession, id: int) -> None:
        """根据ID删除AI历史记录"""
        statement = select(AiHistory).where(AiHistory.id == id)
        result = await db.execute(statement)
        history = result.scalar_one_or_none()
        if history:
            await db.delete(history)
            await db.commit()


@lru_cache()
def get_ai_history_mapper() -> AiHistoryMapper:
    return AiHistoryMapper()
