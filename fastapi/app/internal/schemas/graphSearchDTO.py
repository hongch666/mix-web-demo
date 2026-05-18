from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from .alias import Alias


class GraphSearchEnhanceReq(BaseModel):
    """图谱搜索增强请求"""
    model_config = {"populate_by_name": True}

    userId: Optional[int] = Alias("userId", default=None)
    keyword: str = ""
    articleIds: List[int] = Alias("articleIds", default_factory=list)
    categoryName: str = Alias("categoryName", default="")
    subCategoryName: str = Alias("subCategoryName", default="")
    tags: List[str] = Field(default_factory=list)
    limit: int = 50
    mode: str = "hybrid"


class GraphRelationDTO(BaseModel):
    """图谱关系"""
    type: str
    name: str
    score: float
    reason: str


class GraphSearchEnhanceItemDTO(BaseModel):
    """图谱增强单项结果"""
    model_config = {"populate_by_name": True}

    articleId: int = Alias("articleId")
    graphScore: float = Alias("graphScore")
    reason: str
    relations: List[GraphRelationDTO] = Field(default_factory=list)
    matchedTags: List[str] = Alias("matchedTags", default_factory=list)
    matchedPaths: List[str] = Alias("matchedPaths", default_factory=list)


class GraphSearchEnhanceResp(BaseModel):
    """图谱搜索增强响应"""
    items: List[GraphSearchEnhanceItemDTO] = Field(default_factory=list)
