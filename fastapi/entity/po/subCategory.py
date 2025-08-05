from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class SubCategory(SQLModel, table=True):
    __tablename__ = "sub_category"
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    name: str
    category_id: Optional[int] = None  # 所属分类ID
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None