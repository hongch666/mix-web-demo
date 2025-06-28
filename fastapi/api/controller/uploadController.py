from fastapi import APIRouter
from entity.dto.uploadDTO import UploadDTO
from common.middleware.ContextMiddleware import get_current_user_id, get_current_username
from api.service.analyzeService import upload_file
from common.utils.response import success
from common.utils.writeLog import fileLogger
from starlette.concurrency import run_in_threadpool
from typing import Any

router: APIRouter = APIRouter(
    prefix="/upload",
    tags=["上传文件接口"],
)

@router.post("")
async def get_wordcloud(data: UploadDTO) -> Any:
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    fileLogger.info("用户"+user_id+":"+username+" POST /upload: 上传文件\nUploadDTO: " + data.json())
    oss_url: str = await run_in_threadpool(
        upload_file, 
        data.local_file, 
        data.oss_file
    )
    return success(oss_url)