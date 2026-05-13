from typing import Any

from app.common.decorators import log, requireInternalToken
from app.core.base import success
from app.internal.schemas.vectorSearchDTO import VectorSearchEnhanceReq
from app.internal.services.vectorSearch import (
    VectorSearchService,
    get_vector_search_service,
)

from fastapi import APIRouter, Depends, Request

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
