from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError

from app.core.constants import Messages


class GenerateDTO(BaseModel):
    """生成 DTO"""

    text: str = Field(
        ...,
        description="需要生成标签的文本内容",
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        """校验待生成标签的文本内容不能为空"""
        if not value.strip():
            raise PydanticCustomError("text_empty", Messages.GENERATE_TEXT_EMPTY)
        return value
