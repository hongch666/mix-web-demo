from fastapi import APIRouter
from api.service.generateService import extract_tags
from common.middleware.ContextMiddleware import get_current_user_id, get_current_username
from common.utils.response import success
from common.utils.writeLog import fileLogger
from starlette.concurrency import run_in_threadpool

from entity.dto.generateDTO import GenerateDTO
from typing import Any

router: APIRouter = APIRouter(
    prefix="/generate",
    tags=["生成相关接口"],
)

@router.post("/tags")
async def generate_tags(data: GenerateDTO) -> Any:
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    fileLogger.info("用户" + user_id + ":" + username + " POST /generate/tags: 生成tags\GenerateDTO: " + data.json())
    tags: list[str] = await run_in_threadpool(
        extract_tags, 
        data.text,
    )
    return success(tags)