from sqlmodel import SQLModel, Field
from typing import Optional

class User(SQLModel, table=True):
    __tablename__ = "user"
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    password: str
    name: str
    age: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None
    img: Optional[str] = None
    signature: Optional[str] = None