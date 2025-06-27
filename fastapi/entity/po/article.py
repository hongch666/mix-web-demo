import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Article(Base):
    __tablename__ = "articles"
    id: int = Column(Integer, primary_key=True, index=True)
    title: str = Column(String(255))
    content: str = Column(Text)
    user_id: int = Column(Integer)
    tags: str = Column(String(255))
    status: str = Column(String(255))
    create_at: "datetime.datetime" = Column(DateTime)
    update_at: "datetime.datetime" = Column(DateTime)
    views: int = Column(Integer)