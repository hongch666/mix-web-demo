from functools import lru_cache
from sqlmodel import Session, select

from entity.po import AiHistory

class AiHistoryMapper:
    
    def create_ai_history(self, ai_history: AiHistory, db: Session) -> AiHistory:
        db.add(ai_history)
        db.commit()
        db.refresh(ai_history)
        return ai_history

    def get_all_ai_history_by_userid(self, db: Session, user_id: int, limit: int) -> list[AiHistory]:
        if limit is None:
            statement = select(AiHistory).where(AiHistory.user_id == user_id).order_by(AiHistory.created_at.asc())
        else:
            statement = select(AiHistory).where(AiHistory.user_id == user_id).order_by(AiHistory.created_at.asc()).limit(limit)
        return db.exec(statement).all()

@lru_cache()
def get_ai_history_mapper() -> AiHistoryMapper:
    return AiHistoryMapper()