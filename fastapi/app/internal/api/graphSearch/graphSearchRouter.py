from typing import Any

from app.common.decorators import log, requireInternalToken
from app.core.base import success
from app.internal.schemas.graphSearchDTO import GraphSearchEnhanceReq
from app.internal.services.graphSearch import (
    GraphSearchService,
    get_graph_search_service,
)

from fastapi import APIRouter, Depends, Request

router: APIRouter = APIRouter(
    prefix="/graph-search",
    tags=["知识图谱模块"],
)


@router.post(
    "/enhance",
    summary="知识图谱搜索增强",
    description="根据文章ID列表和用户画像, 返回对应文章的图谱分、推荐原因和关系证据（仅限内部服务调用）",
)
@log("知识图谱搜索增强")
@requireInternalToken
async def graph_search_enhance(
    request: Request,
    req: GraphSearchEnhanceReq,
    graphSearchService: GraphSearchService = Depends(get_graph_search_service),
) -> Any:
    """知识图谱搜索增强接口"""

    result = await graphSearchService.enhance(req)
    return success(result)
