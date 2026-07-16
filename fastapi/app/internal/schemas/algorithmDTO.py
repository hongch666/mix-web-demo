from pydantic import BaseModel, Field


class ScoreWeightItem(BaseModel):
    """单个权重项"""

    key: str
    value: float
    description: str = ""


class SearchWeightsResp(BaseModel):
    """搜索权重响应"""

    weights: list[ScoreWeightItem] = Field(default_factory=list)
