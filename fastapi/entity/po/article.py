from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Article(SQLModel, table=True):
    """文章实体类"""
    
    __tablename__ = "articles"
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    title: str
    content: str
    user_id: Optional[int] = None
    tags: Optional[str] = None
    status: Optional[str] = None
    create_at: Optional[datetime] = None
    update_at: Optional[datetime] = None
    views: Optional[int] = 0
    sub_category_id: Optional[int] = None  # 子分类ID