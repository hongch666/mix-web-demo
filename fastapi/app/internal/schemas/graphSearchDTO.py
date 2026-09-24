from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .alias import Alias


class GraphSearchEnhanceReq(BaseModel):
    """图谱搜索增强请求"""

    model_config = {"populate_by_name": True}

    userId: Optional[int] = Alias("userId", default=None, description="用户ID")
    keyword: str = Field(default="", description="搜索关键词")
    articleIds: list[int] = Alias(
        "articleIds", default_factory=list, description="候选文章ID列表"
    )
    categoryName: str = Alias("categoryName", default="", description="分类名称")
    subCategoryName: str = Alias(
        "subCategoryName", default="", description="子分类名称"
    )
    tags: list[str] = Field(default_factory=list, description="标签列表")
    limit: int = Field(default=50, description="返回条数上限")
    mode: str = Field(
        default="hybrid", description="搜索模式，keyword、hybrid、graph，默认 hybrid"
    )


class GraphRelationDTO(BaseModel):
    """图谱关系"""

    type: str = Field(description="关系类型")
    name: str = Field(description="关系名称")
    score: float = Field(description="关系得分")
    reason: str = Field(description="推荐原因")


class GraphSearchEnhanceItemDTO(BaseModel):
    """图谱增强单项结果"""

    model_config = {"populate_by_name": True}

    articleId: int = Alias("articleId", description="文章ID")
    graphScore: float = Alias("graphScore", description="图谱得分")
    reason: str = Field(description="推荐原因")
    relations: list[GraphRelationDTO] = Field(
        default_factory=list, description="关系证据"
    )
    matchedTags: list[str] = Alias(
        "matchedTags", default_factory=list, description="命中标签"
    )
    matchedPaths: list[str] = Alias(
        "matchedPaths", default_factory=list, description="命中路径"
    )


class GraphSearchEnhanceResp(BaseModel):
    """图谱搜索增强响应"""

    items: list[GraphSearchEnhanceItemDTO] = Field(
        default_factory=list, description="增强结果列表"
    )
