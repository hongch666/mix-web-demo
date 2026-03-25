from app.core.db import Base
from sqlalchemy import Column, Integer, String


class CategoryReference(Base):
    """权威参考文本实体类"""

    __tablename__ = "category_reference"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sub_category_id = Column(Integer, nullable=True, index=True)  # 所属子分类ID
    type = Column(String(50), nullable=True)  # 参考文本类型: link 或 pdf
    link = Column(String(1024), nullable=True)  # 链接地址
    pdf = Column(String(1024), nullable=True)  # PDF 文件地址
