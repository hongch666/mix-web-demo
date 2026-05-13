from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class VectorSearchEnhanceReq(BaseModel):
    """向量搜索增强请求"""

    userId: Optional[int] = None
    keyword: str = ""
    articleIds: List[int] = Field(default_factory=list)
    categoryName: str = ""
    subCategoryName: str = ""
    tags: List[str] = Field(default_factory=list)
    limit: int = 50
    topK: int = 50
    mode: str = "hybrid"


class VectorMatchedChunkDTO(BaseModel):
    """向量匹配片段"""

    articleId: int
    title: str = ""
    chunkIndex: int = 0
    score: float
    content: str = ""


class VectorSearchEnhanceItemDTO(BaseModel):
    """向量增强单项结果"""

    articleId: int
    vectorScore: float
    reason: str = ""
    matchedChunks: List[VectorMatchedChunkDTO] = Field(default_factory=list)


class VectorSearchEnhanceResp(BaseModel):
    """向量搜索增强响应"""

    items: List[VectorSearchEnhanceItemDTO] = Field(default_factory=list)
