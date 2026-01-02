from sqlmodel import SQLModel, Field
from typing import Optional

class Comments(SQLModel, table=True):
    """评论实体类"""
    
    __tablename__ = "comments"
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    content: str
    star: float
    user_id: int
    article_id: int
    create_time: Optional[str] = None
    update_time: Optional[str] = None