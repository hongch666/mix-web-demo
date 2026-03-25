from app.core.db import Base
from sqlalchemy import Column, Float, Integer, String


class Comments(Base):
    """评论实体类"""

    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    content = Column(String(2048), nullable=False)
    star = Column(Float, nullable=False)
    user_id = Column(Integer, nullable=False)
    article_id = Column(Integer, nullable=False)
    create_time = Column(String(64), nullable=True)
    update_time = Column(String(64), nullable=True)
