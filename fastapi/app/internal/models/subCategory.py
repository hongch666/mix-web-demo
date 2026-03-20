from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class SubCategory(SQLModel, table=True):
    """子分类实体类"""

    __tablename__ = "sub_category"
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    name: str = Field()
    category_id: Optional[int] = Field(default=None)  # 所属分类ID
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)
