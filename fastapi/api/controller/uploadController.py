from fastapi import APIRouter, File, UploadFile
from entity.dto.uploadDTO import UploadDTO
from common.middleware.ContextMiddleware import get_current_user_id, get_current_username
from api.service.analyzeService import upload_file
from api.service.uploadService import handle_image_upload
from common.utils.response import success
from common.utils.writeLog import fileLogger
from starlette.concurrency import run_in_threadpool
from typing import Any
import os
import shutil
import uuid

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

@router.post("/image")
async def upload_image_to_oss(file: UploadFile = File(...)) -> Any:
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    fileLogger.info(f"用户{user_id}:{username} POST /upload/image: 上传图片 文件名: {file.filename}")
    file_dict = {
        'filename': file.filename,
        'file': file.file,
        'user_id': user_id,
        'username': username
    }
    result = await handle_image_upload(file_dict)
    return success(result)