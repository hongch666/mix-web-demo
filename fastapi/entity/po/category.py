from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Category(SQLModel, table=True):
    """分类实体类"""
    
    __tablename__ = "category"
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    name: str = Field()
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)