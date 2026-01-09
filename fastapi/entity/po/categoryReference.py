from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class CategoryReference(SQLModel, table=True):
    """权威参考文本实体类"""
    
    __tablename__ = "category_reference"
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    sub_category_id: Optional[int] = Field(default=None, index=True)  # 所属子分类ID
    type: Optional[str] = None  # 参考文本类型: link 或 pdf
    link: Optional[str] = None  # 链接地址
    pdf: Optional[str] = None  # PDF 文件地址
