from pydantic import BaseModel, Field

class GenerateDTO(BaseModel):
    text: str = Field(
        ...,
        description="需要生成标签的文本内容",
    )