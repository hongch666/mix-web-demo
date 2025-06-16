from fastapi import APIRouter
from dto.uploadDTO import UploadDTO
from service.analyzeService import upload_file
from utils.response import success
from utils.logger import logger
from starlette.concurrency import run_in_threadpool

router = APIRouter(
    prefix="/upload",
    tags=["上传文件接口"],
)

@router.post("")
async def get_wordcloud(data: UploadDTO):
    logger.info("/upload: 上传文件\nUploadDTO: " + data.json())
    oss_url = await run_in_threadpool(
        upload_file, 
        data.local_file, 
        data.oss_file
    )
    return success(oss_url)