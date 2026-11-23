from datetime import datetime

from sqlalchemy import DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AiUserSummary(Base):
    """用户级聊天记忆摘要实体类"""

    __tablename__ = "ai_user_summary"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, nullable=False, unique=True, index=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # 已折叠进摘要的历史记录最大 id，作为增量压缩的水位线
    last_summarized_history_id: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    summarized_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=datetime.now
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=datetime.now
    )
