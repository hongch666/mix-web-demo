from typing import Any

from app.common.decorators import log, requireInternalToken
from app.core.base import success
from app.internal.services.algorithm import (
    AlgorithmService,
    get_algorithm_service,
)

from fastapi import APIRouter, Depends, Request

router = APIRouter(prefix="/algorithm", tags=["算法模块"])


@router.get(
    "/search/weights",
    summary="获取搜索排序权重配置",
    description="返回 ES 复合打分和融合排序所需的全量权重参数（仅限内部服务调用）",
)
@log("获取搜索权重")
@requireInternalToken
async def get_search_weights(
    request: Request,
    algorithm_service: AlgorithmService = Depends(get_algorithm_service),
) -> Any:
    result = algorithm_service.get_weights()
    return success(result)
