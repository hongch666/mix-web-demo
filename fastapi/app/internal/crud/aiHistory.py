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
        """按用户查询历史记录

        limit 为空时按时间正序返回全部记录，供历史列表展示使用；
        指定 limit 时先按时间倒序取最近 limit 条，再反转为正序返回，
        保证调用方拿到的是"最近的记录"且按旧到新排列
        """
        if limit is None:
            statement = (
                select(AiHistory)
                .where(AiHistory.user_id == user_id)
                .order_by(AiHistory.created_at.asc(), AiHistory.id.asc())
            )
            return list((await db.execute(statement)).scalars().all())

        statement = (
            select(AiHistory)
            .where(AiHistory.user_id == user_id)
            .order_by(AiHistory.created_at.desc(), AiHistory.id.desc())
            .limit(limit)
        )
        recent_histories = list((await db.execute(statement)).scalars().all())
        # 数据库侧按倒序取最近记录，这里反转为正序，供上下文按旧到新拼接
        recent_histories.reverse()
        return recent_histories

    async def get_ai_history_after_id_async(
        self, db: AsyncSession, user_id: int, after_id: int, limit: int
    ) -> list[AiHistory]:
        """取压缩水位线之后的历史记录

        先按 id 倒序取最近的 limit 条，再反转为正序返回，
        保证返回的是最新一批且按旧到新排列
        """
        statement = (
            select(AiHistory)
            .where(AiHistory.user_id == user_id, AiHistory.id > after_id)
            .order_by(AiHistory.id.desc())
            .limit(limit)
        )
        recent_histories = list((await db.execute(statement)).scalars().all())
        recent_histories.reverse()
        return recent_histories

    async def get_oldest_ai_history_after_id_async(
        self, db: AsyncSession, user_id: int, after_id: int, limit: int
    ) -> list[AiHistory]:
        """取压缩水位线之后最早的若干条历史记录

        正向读取水位线之后最旧的一批，供候选上限跳过的更早记录补进摘要，
        与取最近一批的 get_ai_history_after_id_async 互补
        """
        statement = (
            select(AiHistory)
            .where(AiHistory.user_id == user_id, AiHistory.id > after_id)
            .order_by(AiHistory.id.asc())
            .limit(limit)
        )
        return list((await db.execute(statement)).scalars().all())

    async def delete_ai_history_by_userid_async(
        self, db: AsyncSession, user_id: int
    ) -> None:
        """按用户删除历史记录

        只提交到会话，事务由调用方统一提交，便于与记忆摘要删除保持原子
        """
        statement = select(AiHistory).where(AiHistory.user_id == user_id)
        histories = (await db.execute(statement)).scalars().all()
        for history in histories:
            await db.delete(history)
        await db.flush()

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


@lru_cache
def get_ai_history_mapper() -> AiHistoryMapper:
    return AiHistoryMapper()
