from sqlmodel import SQLModel, Field
from typing import Optional

class User(SQLModel, table=True):
    """用户实体类"""
    
    __tablename__ = "user"
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    password: str = Field()
    name: str = Field()
    age: Optional[int] = Field(default=None)
    email: Optional[str] = Field(default=None)
    role: Optional[str] = Field(default=None)
    img: Optional[str] = Field(default=None)
    signature: Optional[str] = Field(default=None)