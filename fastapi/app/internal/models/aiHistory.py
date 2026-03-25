from datetime import datetime

from app.core.db import Base
from sqlalchemy import Column, DateTime, Integer, String, Text


class AiHistory(Base):
    """AI 历史记录实体类"""

    __tablename__ = "ai_history"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    ask = Column(Text, nullable=False, default="")
    reply = Column(Text, nullable=False, default="")
    thinking = Column(Text, nullable=True)
    ai_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=True, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, default=datetime.now)
