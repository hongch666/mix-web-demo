from app.core.db import Base
from sqlalchemy import Column, DateTime, Integer, String, Text


class Article(Base):
    """文章实体类"""

    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, nullable=True)
    tags = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True)
    create_at = Column(DateTime, nullable=True)
    update_at = Column(DateTime, nullable=True)
    views = Column(Integer, default=0, nullable=False)
    sub_category_id = Column(Integer, nullable=True)  # 子分类ID
