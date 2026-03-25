from datetime import datetime

from app.core.db.base import Base
from sqlalchemy import Column, DateTime, Integer


class Focus(Base):
    """关注实体类"""

    __tablename__ = "focus"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    focus_id = Column(Integer, nullable=False)
    created_time = Column(DateTime, nullable=True, default=datetime.now)
