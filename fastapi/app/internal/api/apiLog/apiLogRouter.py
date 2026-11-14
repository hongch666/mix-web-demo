from typing import Any

from fastapi import APIRouter, Request

from app.core.base import ApiResponse, success
from app.core.decorators import log, requireAdmin
from app.dependencies import ApiLogServiceDep
from app.internal.schemas import ApiLogAverageResponse, ApiLogCalledCountResponse

router: APIRouter = APIRouter(
    prefix="/analyze/api",
    tags=["API日志分析模块"],
)


@router.get(
    "/average-speed",
    summary="获取所有接口的平均响应速度",
    description="返回各接口的平均响应耗时与调用次数，数据来自 ClickHouse 的 API 日志聚合，未命中缓存时回退到 NestJS 实时查询",
    response_model=ApiResponse[list[ApiLogAverageResponse]],
)
@log("获取所有接口的平均响应速度")
@requireAdmin
async def get_api_average_speed(
    request: Request, apilogService: ApiLogServiceDep
) -> ApiResponse:
    """获取所有接口的平均响应速度"""

    result: list[
        dict[str, Any]
    ] = await apilogService.get_api_average_response_time_service()
    return success(result)


@router.get(
    "/called-count",
    summary="获取接口调用次数",
    description="返回各接口的调用次数（同时带出平均响应耗时），数据来源与平均响应速度接口一致",
    response_model=ApiResponse[list[ApiLogCalledCountResponse]],
)
@log("获取接口调用次数")
@requireAdmin
async def get_called_count_apis(
    request: Request, apilogService: ApiLogServiceDep
) -> ApiResponse:
    """获取接口调用次数"""

    result: list[dict[str, Any]] = await apilogService.get_called_count_apis_service()
    return success(result)
