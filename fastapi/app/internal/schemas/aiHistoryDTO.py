from typing import Optional

from pydantic import BaseModel, Field


class AiHistoryResponse(BaseModel):
    """AI 历史记录"""

    id: int = Field(description="记录 ID")
    user_id: int = Field(description="用户 ID")
    ask: str = Field(description="用户提问")
    reply: str = Field(description="模型回复")
    thinking: Optional[str] = Field(default=None, description="模型思考过程")
    ai_type: str = Field(description="AI 服务类型")
    created_at: Optional[str] = Field(default=None, description="创建时间")
    updated_at: Optional[str] = Field(default=None, description="更新时间")
