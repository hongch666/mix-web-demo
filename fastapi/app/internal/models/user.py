from app.core.db.base import Base
from sqlalchemy import Column, Integer, String


class User(Base):
    """用户实体类"""

    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)
    email = Column(String(255), nullable=True)
    role = Column(String(50), nullable=True)
    img = Column(String(512), nullable=True)
    signature = Column(String(512), nullable=True)
