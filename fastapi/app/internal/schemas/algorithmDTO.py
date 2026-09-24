from pydantic import BaseModel, Field


class ScoreWeightItem(BaseModel):
    """单个搜索权重项"""

    key: str = Field(description="权重键")
    value: float = Field(description="权重值")
    description: str = Field(default="", description="权重说明")


class SearchScriptResponse(BaseModel):
    """ES 搜索脚本响应 — 包含使用 params.xxx 占位符的 Painless 脚本，由调用方传入权重参数后使用"""

    es_script: str = Field(description="ES Painless 搜索脚本")


class ScriptParamItem(BaseModel):
    """脚本参数名映射项 — 将权重 key 映射到 Painless 脚本中的实际参数名"""

    weight_key: str = Field(description="权重键")
    param_name: str = Field(description="脚本参数名")
    description: str = Field(default="", description="参数说明")
