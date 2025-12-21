from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Collect(SQLModel, table=True):
    __tablename__ = "collects"
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    article_id: int = Field(index=True)
    user_id: int = Field(index=True)
    created_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
