from app.core.db.base import Base
from sqlalchemy import Column, DateTime, Integer, String


class SubCategory(Base):
    """子分类实体类"""

    __tablename__ = "sub_category"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    category_id = Column(Integer, nullable=True)  # 所属分类ID
    create_time = Column(DateTime, nullable=True)
    update_time = Column(DateTime, nullable=True)
