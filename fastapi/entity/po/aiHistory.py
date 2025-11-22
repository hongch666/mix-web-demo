from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Text

class AiHistory(SQLModel, table=True):
    __tablename__ = "ai_history"
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: Optional[int] = None
    ask: str = Field(default="", sa_column=Column(Text))
    reply: str = Field(default="", sa_column=Column(Text))
    thinking: Optional[str] = Field(default=None, sa_column=Column(Text))
    ai_type: str
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
    