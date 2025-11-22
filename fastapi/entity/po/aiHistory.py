from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class AiHistory(SQLModel, table=True):
    __tablename__ = "ai_history"
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: Optional[int] = None
    ask: str = Field(default="")
    reply: str = Field(default="")
    thinking: Optional[str] = Field(default=None)
    ai_type: str
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
    