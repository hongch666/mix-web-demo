from fastapi import APIRouter
from api.service.generateService import extract_tags
from common.middleware.ContextMiddleware import get_current_user_id, get_current_username
from common.utils.response import success
from common.utils.logger import logger
from starlette.concurrency import run_in_threadpool

from entity.dto.generateDTO import GenerateDTO

router = APIRouter(
    prefix="/generate",
    tags=["生成相关接口"],
)

@router.post("/tags")
async def generate_tags(data: GenerateDTO):
    user_id = get_current_user_id() or ""
    username = get_current_username() or ""
    logger.info("用户"+user_id+":"+username+" POST /generate/tags: 生成tags\GenerateDTO: " + data.json())
    tags = await run_in_threadpool(
        extract_tags, 
        data.text,
    )
    return success(tags)