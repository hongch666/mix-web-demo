from fastapi import APIRouter, Depends, Request
from typing import Any
from starlette.concurrency import run_in_threadpool
from api.service import GenerateService, get_generate_service
from common.utils import success
from common.decorators import log
from entity.dto import GenerateDTO

router: APIRouter = APIRouter(
    prefix="/generate",
    tags=["生成相关接口"],
)

@router.post(
    "/tags",
    summary="生成tags",
    description="根据输入文本生成tags数组"
)
@log("生成tags")
async def generate_tags(request: Request, data: GenerateDTO, generateService: GenerateService = Depends(get_generate_service)) -> Any:
    tags: list[str] = await run_in_threadpool(
        generateService.extract_tags,
        data.text,
    )
    return success(tags)