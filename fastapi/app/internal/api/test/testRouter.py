from fastapi import APIRouter, Request

from app.core.base import ApiResponse, success
from app.core.constants import Messages
from app.core.decorators import log

router: APIRouter = APIRouter(
    prefix="/test",
    tags=["测试模块"],
)


# 测试FastAPI服务
@router.get(
    "/fastapi",
    summary="测试FastAPI服务",
    description="验证 FastAPI 服务是否正常运行，成功时返回欢迎文案 Hello, I am FastAPI!",
    response_model=ApiResponse[str],
)
@log("测试FastAPI服务")
async def testFastapi(request: Request) -> ApiResponse:
    """测试FastAPI服务接口"""
    return success(Messages.TEST_MESSAGE)
