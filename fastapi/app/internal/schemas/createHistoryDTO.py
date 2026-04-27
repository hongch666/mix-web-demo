from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError


class CreateHistoryDTO(BaseModel):
    """创建历史记录 DTO"""

    user_id: int = Field(
        ...,
        description="用户ID",
    )
    ask: str = Field(
        ...,
        description="用户提问内容",
    )
    reply: str = Field(
        ...,
        description="AI回复内容",
    )
    thinking: str | None = Field(
        default=None,
        description="AI思考过程，可选",
    )
    ai_type: str = Field(
        ...,
        description="AI类型（例：gpt、gemini、deepseek等）",
    )

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, value: int) -> int:
        if value <= 0:
            raise PydanticCustomError("user_id_error", "用户ID必须大于0")
        return value

    @field_validator("ask")
    @classmethod
    def validate_ask(cls, value: str) -> str:
        if not value.strip():
            raise PydanticCustomError("ask_error", "用户提问内容不能为空")
        return value

    @field_validator("reply")
    @classmethod
    def validate_reply(cls, value: str) -> str:
        if not value.strip():
            raise PydanticCustomError("reply_error", "AI回复内容不能为空")
        return value

    @field_validator("ai_type")
    @classmethod
    def validate_ai_type(cls, value: str) -> str:
        if not value.strip():
            raise PydanticCustomError("ai_type_empty", "AI类型不能为空")
        if len(value) > 50:
            raise PydanticCustomError("ai_type_length", "AI类型长度不能超过50个字符")
        return value
