from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, Text

from app.core.db import Base


class AiUserSummary(Base):
    """用户级聊天记忆摘要实体类"""

    __tablename__ = "ai_user_summary"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    summary = Column(Text, nullable=False, default="")
    # 已折叠进摘要的历史记录最大 id，作为增量压缩的水位线
    last_summarized_history_id = Column(Integer, nullable=False, default=0)
    summarized_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=True, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, default=datetime.now)
