from typing import Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError

from .alias import Alias


class UpdateHistoryDTO(BaseModel):
    """更新历史记录 DTO"""

    model_config = {"populate_by_name": True}

    userId: Optional[int] = Alias(
        "userId",
        default=None,
        description="用户ID",
    )
    ask: Optional[str] = Field(
        default=None,
        description="用户提问内容",
    )
    reply: Optional[str] = Field(
        default=None,
        description="AI回复内容",
    )
    thinking: Optional[str] = Field(
        default=None,
        description="AI思考过程，可选",
    )
    aiType: Optional[str] = Alias(
        "aiType",
        default=None,
        description="AI类型（例：gpt、gemini、glm等）",
    )

    @field_validator("userId")
    @classmethod
    def validate_user_id(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value <= 0:
            raise PydanticCustomError("user_id_error", "用户ID必须大于0")
        return value

    @field_validator("ask")
    @classmethod
    def validate_ask(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise PydanticCustomError("ask_error", "用户提问内容不能为空")
        return value

    @field_validator("reply")
    @classmethod
    def validate_reply(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise PydanticCustomError("reply_error", "AI回复内容不能为空")
        return value

    @field_validator("aiType")
    @classmethod
    def validate_ai_type(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            if not value.strip():
                raise PydanticCustomError("ai_type_empty", "AI类型不能为空")
            if len(value) > 50:
                raise PydanticCustomError(
                    "ai_type_length", "AI类型长度不能超过50个字符"
                )
        return value
