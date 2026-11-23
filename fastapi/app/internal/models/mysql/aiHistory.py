from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AiHistory(Base):
    """AI 历史记录实体类"""

    __tablename__ = "ai_history"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ask: Mapped[str] = mapped_column(Text, nullable=False, default="")
    reply: Mapped[str] = mapped_column(Text, nullable=False, default="")
    thinking: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=datetime.now
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=datetime.now
    )
