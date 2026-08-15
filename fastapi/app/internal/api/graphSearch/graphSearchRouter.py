from app.common.decorators import log, requireInternalToken
from app.core.base import ApiResponse, success
from app.dependencies import GraphSearchServiceDep
from app.internal.schemas import GraphSearchEnhanceReq, GraphSearchEnhanceResp

from fastapi import APIRouter, Request

router: APIRouter = APIRouter(
    prefix="/graph-search",
    tags=["知识图谱模块"],
)


@router.post(
    "/enhance",
    summary="知识图谱搜索增强",
    description="根据文章ID列表和用户画像, 返回对应文章的图谱分、推荐原因和关系证据（仅限内部服务调用）",
    response_model=ApiResponse,
)
@log("知识图谱搜索增强")
@requireInternalToken
async def graph_search_enhance(
    request: Request,
    req: GraphSearchEnhanceReq,
    graphSearchService: GraphSearchServiceDep,
) -> ApiResponse:
    """知识图谱搜索增强接口"""

    result: GraphSearchEnhanceResp = await graphSearchService.enhance(req)
    return success(result)
