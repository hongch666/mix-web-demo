from functools import lru_cache
from typing import List, Optional

from app.internal.models import AiHistory
from sqlalchemy import select
from sqlalchemy.orm import Session


class AiHistoryMapper:
    """AI 历史记录 Mapper"""

    async def _create_ai_history_sync(
        self, ai_history: AiHistory, db: Session
    ) -> AiHistory:
        db.add(ai_history)
        db.commit()
        db.refresh(ai_history)
        return ai_history

    async def _get_all_ai_history_by_userid_sync(
        self, db: Session, user_id: int, limit: Optional[int]
    ) -> List[AiHistory]:
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
        return db.execute(statement).scalars().all()

    async def _delete_ai_history_by_userid_sync(
        self, db: Session, user_id: int
    ) -> None:
        statement = select(AiHistory).where(AiHistory.user_id == user_id)
        histories = db.execute(statement).scalars().all()
        for history in histories:
            db.delete(history)
        db.commit()

    async def create_ai_history_async(
        self, ai_history: AiHistory, db: Session
    ) -> AiHistory:
        return await self._create_ai_history_sync(ai_history, db)

    async def get_all_ai_history_by_userid_async(
        self, db: Session, user_id: int, limit: Optional[int]
    ) -> List[AiHistory]:
        return await self._get_all_ai_history_by_userid_sync(db, user_id, limit)

    async def delete_ai_history_by_userid_async(
        self, db: Session, user_id: int
    ) -> None:
        await self._delete_ai_history_by_userid_sync(db, user_id)


@lru_cache()
def get_ai_history_mapper() -> AiHistoryMapper:
    return AiHistoryMapper()
