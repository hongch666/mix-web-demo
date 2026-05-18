from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from .alias import Alias


class VectorSearchEnhanceReq(BaseModel):
    """向量搜索增强请求"""
    model_config = {"populate_by_name": True}

    userId: Optional[int] = Alias("userId", default=None)
    keyword: str = ""
    articleIds: List[int] = Alias("articleIds", default_factory=list)
    categoryName: str = Alias("categoryName", default="")
    subCategoryName: str = Alias("subCategoryName", default="")
    tags: List[str] = Field(default_factory=list)
    limit: int = 50
    topK: int = Alias("topK", default=50)
    mode: str = "hybrid"


class VectorMatchedChunkDTO(BaseModel):
    """向量匹配片段"""
    model_config = {"populate_by_name": True}

    articleId: int = Alias("articleId")
    title: str = ""
    chunkIndex: int = Alias("chunkIndex", default=0)
    score: float
    content: str = ""


class VectorSearchEnhanceItemDTO(BaseModel):
    """向量增强单项结果"""
    model_config = {"populate_by_name": True}

    articleId: int = Alias("articleId")
    vectorScore: float = Alias("vectorScore")
    reason: str = ""
    matchedChunks: List[VectorMatchedChunkDTO] = Alias(
        "matchedChunks", default_factory=list
    )


class VectorSearchEnhanceResp(BaseModel):
    """向量搜索增强响应"""

    items: List[VectorSearchEnhanceItemDTO] = Field(default_factory=list)
