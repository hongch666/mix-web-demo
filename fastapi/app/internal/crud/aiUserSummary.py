from datetime import datetime
from functools import lru_cache
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.internal.models import AiUserSummary


class AiUserSummaryMapper:
    """用户级聊天记忆摘要 Mapper"""

    async def get_by_user_id_async(
        self, db: AsyncSession, user_id: int
    ) -> Optional[AiUserSummary]:
        """按用户查询记忆摘要，未生成过摘要时返回空"""
        statement = select(AiUserSummary).where(AiUserSummary.user_id == user_id)
        return (await db.execute(statement)).scalar_one_or_none()

    async def upsert_async(
        self,
        db: AsyncSession,
        user_id: int,
        summary: str,
        last_summarized_history_id: int,
        summarized_count: int,
    ) -> AiUserSummary:
        """写入摘要并推进压缩水位线，同一用户只保留一行"""
        existing = await self.get_by_user_id_async(db, user_id)
        if existing is None:
            record = AiUserSummary(
                user_id=user_id,
                summary=summary,
                last_summarized_history_id=last_summarized_history_id,
                summarized_count=summarized_count,
            )
            db.add(record)
        else:
            existing.summary = summary
            existing.last_summarized_history_id = last_summarized_history_id
            existing.summarized_count = summarized_count
            existing.updated_at = datetime.now()
            record = existing

        await db.commit()
        await db.refresh(record)
        return record

    async def delete_by_user_id_async(self, db: AsyncSession, user_id: int) -> None:
        """清空用户记忆摘要，与历史记录删除联动

        只提交到会话，事务由调用方统一提交，便于与历史记录删除保持原子
        """
        existing = await self.get_by_user_id_async(db, user_id)
        if existing is None:
            return
        await db.delete(existing)
        await db.flush()


@lru_cache
def get_ai_user_summary_mapper() -> AiUserSummaryMapper:
    return AiUserSummaryMapper()
