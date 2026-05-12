from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class GraphSearchEnhanceReq(BaseModel):
    """图谱搜索增强请求"""
    userId: Optional[int] = None
    keyword: str = ""
    articleIds: List[int] = Field(default_factory=list)
    categoryName: str = ""
    subCategoryName: str = ""
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
    articleId: int
    graphScore: float
    reason: str
    relations: List[GraphRelationDTO] = Field(default_factory=list)
    matchedTags: List[str] = Field(default_factory=list)
    matchedPaths: List[str] = Field(default_factory=list)


class GraphSearchEnhanceResp(BaseModel):
    """图谱搜索增强响应"""
    items: List[GraphSearchEnhanceItemDTO] = Field(default_factory=list)
