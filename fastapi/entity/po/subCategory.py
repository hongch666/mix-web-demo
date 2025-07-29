import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SubCategory(Base):
    __tablename__ = "sub_category"
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String(255))
    category_id: int = Column(Integer)  # 所属分类ID
    create_time: "datetime.datetime" = Column(DateTime)
    update_time: "datetime.datetime" = Column(DateTime)