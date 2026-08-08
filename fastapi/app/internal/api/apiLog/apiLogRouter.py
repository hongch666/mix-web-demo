from typing import Any, Dict, List

from app.common.decorators import log, requireAdmin
from app.core.base import success
from app.core.base.response import ApiResponse
from app.internal.services import ApiLogService, get_apilog_service

from fastapi import APIRouter, Depends, Request

router: APIRouter = APIRouter(
    prefix="/analyze/api",
    tags=["API日志分析模块"],
)


@router.get(
    "/average-speed",
    summary="获取所有接口的平均响应速度",
    description="获取所有接口的平均响应速度",
    response_model=ApiResponse,
)
@log("获取所有接口的平均响应速度")
@requireAdmin
async def get_api_average_speed(
    request: Request, apilogService: ApiLogService = Depends(get_apilog_service)
) -> ApiResponse:
    """获取所有接口的平均响应速度"""

    result: List[
        Dict[str, Any]
    ] = await apilogService.get_api_average_response_time_service()
    return success(result)


@router.get(
    "/called-count",
    summary="获取接口调用次数",
    description="获取接口调用次数",
    response_model=ApiResponse,
)
@log("获取接口调用次数")
@requireAdmin
async def get_called_count_apis(
    request: Request, apilogService: ApiLogService = Depends(get_apilog_service)
) -> ApiResponse:
    """获取接口调用次数"""

    result: List[Dict[str, Any]] = await apilogService.get_called_count_apis_service()
    return success(result)
