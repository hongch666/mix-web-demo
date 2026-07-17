from pydantic import BaseModel


class ScoreWeightItem(BaseModel):
    """单个搜索权重项"""

    key: str
    value: float
    description: str = ""
