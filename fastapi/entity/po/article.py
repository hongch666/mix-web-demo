from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Article(SQLModel, table=True):
    """文章实体类"""

    __tablename__ = "articles"
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    title: str = Field()
    content: str = Field()
    user_id: Optional[int] = Field(default=None)
    tags: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    create_at: Optional[datetime] = Field(default=None)
    update_at: Optional[datetime] = Field(default=None)
    views: Optional[int] = Field(default=0)
    sub_category_id: Optional[int] = Field(default=None)  # 子分类ID