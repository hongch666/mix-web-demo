from fastapi import APIRouter, Depends
from api.service import GenerateService, get_generate_service
from common.utils import success
from common.decorators import log
from starlette.concurrency import run_in_threadpool

from entity.dto import GenerateDTO
from typing import Any

router: APIRouter = APIRouter(
    prefix="/generate",
    tags=["生成相关接口"],
)

@router.post("/tags")
@log("生成tags")
async def generate_tags(data: GenerateDTO, generateService: GenerateService = Depends(get_generate_service)) -> Any:
    tags: list[str] = await run_in_threadpool(
        generateService.extract_tags,
        data.text,
    )
    return success(tags)