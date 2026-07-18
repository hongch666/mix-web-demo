from pydantic import BaseModel


class ScoreWeightItem(BaseModel):
    """单个搜索权重项"""

    key: str
    value: float
    description: str = ""


class SearchScriptResponse(BaseModel):
    """ES 搜索脚本响应 — 包含使用 params.xxx 占位符的 Painless 脚本，由调用方传入权重参数后使用"""

    es_script: str
