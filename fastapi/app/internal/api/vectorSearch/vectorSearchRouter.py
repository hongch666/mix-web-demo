from app.common.decorators import log, requireInternalToken
from app.core.base import success
from app.core.base.response import ApiResponse
from app.dependencies import VectorSearchServiceDep
from app.internal.schemas.vectorSearchDTO import VectorSearchEnhanceReq

from fastapi import APIRouter, Request

router: APIRouter = APIRouter(
    prefix="/vector-search",
    tags=["向量搜索模块"],
)


@router.post(
    "/enhance",
    summary="向量搜索增强",
    description="根据 ES 候选文章和搜索词返回语义分、语义原因和匹配片段（仅限内部服务调用）",
    response_model=ApiResponse,
)
@log("向量搜索增强")
@requireInternalToken
async def vector_search_enhance(
    request: Request,
    req: VectorSearchEnhanceReq,
    vectorSearchService: VectorSearchServiceDep,
) -> ApiResponse:
    """向量搜索增强接口"""

    result = await vectorSearchService.enhance(req)
    return success(result)
