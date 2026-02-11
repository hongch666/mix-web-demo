from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Request
from starlette.concurrency import run_in_threadpool
from api.service import get_apilog_service, ApiLogService
from common.decorators import log, requireAdmin
from common.utils import success

router: APIRouter = APIRouter(
    prefix="/analyze/api",
    tags=["API日志分析接口"],
)

@router.get(
    "/average-speed",
    summary="获取所有接口的平均响应速度",
    description="获取所有接口的平均响应速度"
)
@log("获取所有接口的平均响应速度")
@requireAdmin
async def get_api_average_speed(
    _: Request, 
    apilogService: ApiLogService = Depends(get_apilog_service)
) -> Any:
    """获取所有接口的平均响应速度"""
    
    result: List[Dict[str, Any]] = await run_in_threadpool(apilogService.get_api_average_response_time_service)
    return success(result)

@router.get(
    "/called-count",
    summary="获取接口调用次数",
    description="获取接口调用次数"
)
@log("获取接口调用次数")
@requireAdmin
async def get_called_count_apis(
    _: Request, 
    apilogService: ApiLogService = Depends(get_apilog_service)
) -> Any:
    """获取接口调用次数"""
    
    result: List[Dict[str, Any]] = await run_in_threadpool(apilogService.get_called_count_apis_service)
    return success(result)