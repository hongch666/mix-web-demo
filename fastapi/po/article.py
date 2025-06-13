from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    content = Column(Text)
    user_id = Column(Integer)
    tags = Column(String(255))
    status = Column(String(255))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    views = Column(Integer)