from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Focus(SQLModel, table=True):
    """关注实体类"""
    
    __tablename__ = "focus"
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: int
    focus_id: int
    created_time: Optional[datetime] = Field(default_factory=datetime.now)
