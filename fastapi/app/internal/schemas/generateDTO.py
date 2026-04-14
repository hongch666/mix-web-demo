from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError


class GenerateDTO(BaseModel):
    """生成 DTO"""

    text: str = Field(
        ...,
        description="需要生成标签的文本内容",
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        if not value.strip():
            raise PydanticCustomError("text_empty", "需要生成标签的文本内容不能为空")
        return value
