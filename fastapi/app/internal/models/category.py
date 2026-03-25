from app.core.db import Base
from sqlalchemy import Column, DateTime, Integer, String


class Category(Base):
    """分类实体类"""

    __tablename__ = "category"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    create_time = Column(DateTime, nullable=True)
    update_time = Column(DateTime, nullable=True)
