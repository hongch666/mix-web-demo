from datetime import datetime

from app.core.db.base import Base
from sqlalchemy import Column, DateTime, Integer


class Collect(Base):
    """收藏实体类"""

    __tablename__ = "collects"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    article_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    created_time = Column(DateTime, nullable=True, default=datetime.utcnow)
