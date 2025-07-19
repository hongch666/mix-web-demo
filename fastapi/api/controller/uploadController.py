from fastapi import APIRouter, File, UploadFile
from entity.dto.uploadDTO import UploadDTO
from common.middleware.ContextMiddleware import get_current_user_id, get_current_username
from api.service.analyzeService import upload_file
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
    """上传图片到阿里云OSS"""
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    fileLogger.info(f"用户{user_id}:{username} POST /upload/image: 上传图片 文件名: {file.filename}")

    # 生成随机UUID作为文件名，保留原文件扩展名
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    
    # 保存到本地临时目录
    save_dir = "tmp/upload"
    os.makedirs(save_dir, exist_ok=True)
    local_path = os.path.join(save_dir, unique_filename)
    
    with open(local_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 上传到阿里云OSS，使用UUID文件名
    oss_path = f"pic/{unique_filename}"
    oss_url: str = await run_in_threadpool(upload_file, local_path, oss_path)

    # 删除本地临时文件
    try:
        os.remove(local_path)
    except Exception as e:
        fileLogger.warning(f"删除临时文件失败: {e}")

    return success({
        "original_filename": file.filename,
        "oss_filename": unique_filename,
        "oss_url": oss_url
    })