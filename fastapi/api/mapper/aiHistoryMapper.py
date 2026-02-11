from functools import lru_cache
from typing import List, Optional
from sqlmodel import Session, select
from entity.po import AiHistory

class AiHistoryMapper:
    """AI 历史记录 Mapper"""
    
    def create_ai_history(self, ai_history: AiHistory, db: Session) -> AiHistory:
        db.add(ai_history)
        db.commit()
        db.refresh(ai_history)
        return ai_history

    def get_all_ai_history_by_userid(self, db: Session, user_id: int, limit: Optional[int]) -> List[AiHistory]:
        if limit is None:
            statement = select(AiHistory).where(AiHistory.user_id == user_id).order_by(AiHistory.created_at.asc())
        else:
            statement = select(AiHistory).where(AiHistory.user_id == user_id).order_by(AiHistory.created_at.asc()).limit(limit)
        return db.exec(statement).all()
    
    def delete_ai_history_by_userid(self, db: Session, user_id: int) -> None:
        statement = select(AiHistory).where(AiHistory.user_id == user_id)
        histories = db.exec(statement).all()
        for history in histories:
            db.delete(history)
        db.commit()

@lru_cache()
def get_ai_history_mapper() -> AiHistoryMapper:
    return AiHistoryMapper()