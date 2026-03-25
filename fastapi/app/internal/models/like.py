from datetime import datetime

from app.core.db import Base
from sqlalchemy import Column, DateTime, Integer


class Like(Base):
    """点赞实体类"""

    __tablename__ = "likes"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    article_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    created_time = Column(DateTime, nullable=True, default=datetime.utcnow)
