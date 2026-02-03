from sqlmodel import SQLModel, Field
from typing import Optional

class Comments(SQLModel, table=True):
    """评论实体类"""
    
    __tablename__ = "comments"
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    content: str = Field()
    star: float = Field()
    user_id: int = Field()
    article_id: int = Field()
    create_time: Optional[str] = Field(default=None)
    update_time: Optional[str] = Field(default=None)