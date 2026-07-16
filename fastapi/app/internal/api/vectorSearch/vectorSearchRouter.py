from typing import Any

from app.common.decorators import log, requireInternalToken
from app.core.base import success
from app.core.db import get_redis_client
from app.internal.schemas.vectorSearchDTO import VectorSearchEnhanceReq
from app.internal.services.vectorSearch import (
    VectorSearchService,
    get_vector_search_service,
)

from fastapi import APIRouter, Depends, Query, Request

router: APIRouter = APIRouter(
    prefix="/vector-search",
    tags=["向量搜索模块"],
)


@router.post(
    "/enhance",
    summary="向量搜索增强",
    description="根据 ES 候选文章和搜索词返回语义分、语义原因和匹配片段（仅限内部服务调用）",
)
@log("向量搜索增强")
@requireInternalToken
async def vector_search_enhance(
    request: Request,
    req: VectorSearchEnhanceReq,
    vectorSearchService: VectorSearchService = Depends(get_vector_search_service),
) -> Any:
    """向量搜索增强接口"""

    result = await vectorSearchService.enhance(req)
    return success(result)


@router.get(
    "/embed",
    summary="获取搜索词的嵌入向量",
    description="将搜索文本转换为 1024 维嵌入向量，供 ES script_score 计算 cosineSimilarity。带 Redis 缓存（仅限内部服务调用）",
)
@log("获取搜索嵌入向量")
@requireInternalToken
async def get_query_embedding(
    request: Request,
    keyword: str = Query(..., description="搜索关键词"),
    vectorSearchService: VectorSearchService = Depends(get_vector_search_service),
) -> Any:
    """返回搜索词的嵌入向量（Redis 缓存，TTL 1 小时）"""

    redis_client = get_redis_client()
    result = await vectorSearchService.get_query_embedding(keyword, redis_client)
    return success(result)
