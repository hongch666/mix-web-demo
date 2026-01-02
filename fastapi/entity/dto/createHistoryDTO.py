from pydantic import BaseModel, Field

class CreateHistoryDTO(BaseModel):
    """创建历史记录 DTO"""
    
    user_id: int = Field(
        ...,
        description="用户ID",
        gt=0,
    )
    ask: str = Field(
        ...,
        description="用户提问内容",
        min_length=1,
    )
    reply: str = Field(
        ...,
        description="AI回复内容",
        min_length=1,
    )
    ai_type: str = Field(
        ...,
        description="AI类型（例：doubao、gpt、claude等）",
        min_length=1,
        max_length=50,
    )