from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "user"
    id: int = Column(Integer, primary_key=True, index=True)
    password: str = Column(String(255))
    name: str = Column(String(255))
    age: int = Column(Integer)
    email: str = Column(String(255))
    role: str = Column(String(255))