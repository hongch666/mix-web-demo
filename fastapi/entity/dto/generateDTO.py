from pydantic import BaseModel, Field

class GenerateDTO(BaseModel):
    """生成 DTO"""
    
    text: str = Field(
        ...,
        description="需要生成标签的文本内容",
        min_length=1,
    )