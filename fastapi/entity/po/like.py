from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Like(SQLModel, table=True):
    """点赞实体类"""
    
    __tablename__ = "likes"
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    article_id: int = Field(index=True)
    user_id: int = Field(index=True)
    created_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
