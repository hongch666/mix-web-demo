from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Category(SQLModel, table=True):
    __tablename__ = "category"
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    name: str
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None