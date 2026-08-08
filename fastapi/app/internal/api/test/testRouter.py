from app.common.decorators import log
from app.core.base import ApiResponse, success
from app.core.constants import Messages

from fastapi import APIRouter, Request

router: APIRouter = APIRouter(
    prefix="/test",
    tags=["测试模块"],
)


# 测试FastAPI服务
@router.get(
    "/fastapi",
    summary="测试FastAPI服务",
    description="测试FastAPI服务",
    response_model=ApiResponse,
)
@log("测试FastAPI服务")
async def testFastapi(request: Request) -> ApiResponse:
    """测试FastAPI服务接口"""
    return success(Messages.TEST_MESSAGE)
