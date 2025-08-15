from fastapi import APIRouter, Depends, File, UploadFile
from api.service import AnalyzeService, get_analyze_service,UploadService, get_upload_service
from entity.dto import UploadDTO
from common.middleware import get_current_user_id, get_current_username
from common.utils import success,fileLogger
from starlette.concurrency import run_in_threadpool
from typing import Any

router: APIRouter = APIRouter(
    prefix="/upload",
    tags=["上传文件接口"],
)

@router.post("")
async def get_wordcloud(data: UploadDTO, analyzeService: AnalyzeService = Depends(get_analyze_service)) -> Any:
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    fileLogger.info("用户"+user_id+":"+username+" POST /upload: 上传文件\nUploadDTO: " + data.json())
    oss_url: str = await run_in_threadpool(
        analyzeService.upload_file, 
        data.local_file, 
        data.oss_file
    )
    return success(oss_url)

@router.post("/image")
async def upload_image_to_oss(file: UploadFile = File(...),uploadService: UploadService = Depends(get_upload_service)) -> Any:
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    fileLogger.info(f"用户{user_id}:{username} POST /upload/image: 上传图片 文件名: {file.filename}")
    file_dict = {
        'filename': file.filename,
        'file': file.file,
        'user_id': user_id,
        'username': username
    }
    result = await uploadService.handle_image_upload(file_dict)
    return success(result)