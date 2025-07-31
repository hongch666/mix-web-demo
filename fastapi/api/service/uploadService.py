import os
import shutil
import uuid
from typing import Any, Dict
from starlette.concurrency import run_in_threadpool
from api.service import upload_file
from common.utils import fileLogger

async def handle_image_upload(file) -> Dict[str, Any]:
    """处理图片上传的核心逻辑，保存本地临时文件并上传到OSS"""
    
    # 生成随机UUID作为文件名，保留原文件扩展名
    file_extension = os.path.splitext(file['filename'])[1] if file['filename'] else ""
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"

    # 保存到本地临时目录
    save_dir = "tmp/upload"
    os.makedirs(save_dir, exist_ok=True)
    local_path = os.path.join(save_dir, unique_filename)

    with open(local_path, "wb") as buffer:
        shutil.copyfileobj(file['file'], buffer)

    # 上传到阿里云OSS，使用UUID文件名
    oss_path = f"pic/{unique_filename}"
    oss_url: str = await run_in_threadpool(upload_file, local_path, oss_path)

    # 删除本地临时文件
    try:
        os.remove(local_path)
    except Exception as e:
        fileLogger.warning(f"删除临时文件失败: {e}")

    return {
        "original_filename": file['filename'],
        "oss_filename": unique_filename,
        "oss_url": oss_url
    }
