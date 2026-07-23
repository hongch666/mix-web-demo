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
    description="返回 ES 复合打分和融合排序所需的全量权重参数",
)
@log("获取搜索权重")
@requireInternalToken
async def get_search_weights(
    request: Request,
    algorithm_service: AlgorithmService = Depends(get_algorithm_service),
) -> Any:
    result = algorithm_service.get_weights()
    return success(result)


@router.get(
    "/search/script",
    summary="获取 ES 搜索脚本",
    description="返回已嵌入权重参数的 ES Painless 搜索脚本及融合排序权重",
)
@log("获取ES搜索脚本")
@requireInternalToken
async def get_search_script(
    request: Request,
    algorithm_service: AlgorithmService = Depends(get_algorithm_service),
) -> Any:
    result = algorithm_service.get_es_script()
    return success(result)


@router.get(
    "/search/script-params",
    summary="获取脚本参数名映射",
    description="返回每个权重 key 在 Painless 脚本中对应的 params.xxx 参数名，GoZero 端根据此映射关系动态组装脚本参数，无需硬编码参数名常量",
)
@log("获取脚本参数名映射")
@requireInternalToken
async def get_search_script_params(
    request: Request,
    algorithm_service: AlgorithmService = Depends(get_algorithm_service),
) -> Any:
    result = algorithm_service.get_script_params()
    return success(result)
