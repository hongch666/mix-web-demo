from fastapi import APIRouter, Depends
from api.service import GenerateService, get_generate_service
from common.middleware import get_current_user_id, get_current_username
from common.utils import success, fileLogger
from starlette.concurrency import run_in_threadpool

from entity.dto import GenerateDTO
from typing import Any

router: APIRouter = APIRouter(
    prefix="/generate",
    tags=["生成相关接口"],
)

@router.post("/tags")
async def generate_tags(data: GenerateDTO, generateService: GenerateService = Depends(get_generate_service)) -> Any:
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    fileLogger.info("用户" + user_id + ":" + username + " POST /generate/tags: 生成tags\GenerateDTO: " + data.json())
    tags: list[str] = await run_in_threadpool(
        generateService.extract_tags,
        data.text,
    )
    return success(tags)