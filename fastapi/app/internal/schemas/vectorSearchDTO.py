from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .alias import Alias


class VectorSearchEnhanceReq(BaseModel):
    """向量搜索增强请求"""

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
    topK: int = Alias("topK", default=50, description="向量召回条数")
    mode: str = Field(
        default="hybrid", description="搜索模式，keyword、hybrid、graph，默认 hybrid"
    )


class VectorMatchedChunkDTO(BaseModel):
    """向量匹配片段"""

    model_config = {"populate_by_name": True}

    articleId: int = Alias("articleId", description="文章ID")
    title: str = Field(default="", description="文章标题")
    chunkIndex: int = Alias("chunkIndex", default=0, description="片段序号")
    score: float = Field(description="相似度")
    content: str = Field(default="", description="片段内容")


class VectorSearchEnhanceItemDTO(BaseModel):
    """向量增强单项结果"""

    model_config = {"populate_by_name": True}

    articleId: int = Alias("articleId", description="文章ID")
    vectorScore: float = Alias("vectorScore", description="语义得分")
    reason: str = Field(default="", description="推荐原因")
    matchedChunks: list[VectorMatchedChunkDTO] = Alias(
        "matchedChunks", default_factory=list, description="匹配片段"
    )


class VectorSearchEnhanceResp(BaseModel):
    """向量搜索增强响应"""

    items: list[VectorSearchEnhanceItemDTO] = Field(
        default_factory=list, description="增强结果列表"
    )
