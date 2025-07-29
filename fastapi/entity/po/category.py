import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Category(Base):
    __tablename__ = "category"
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String(255))
    create_time: "datetime.datetime" = Column(DateTime)
    update_time: "datetime.datetime" = Column(DateTime)