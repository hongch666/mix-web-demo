from fastapi import APIRouter, Depends, File, Request, UploadFile
from starlette.concurrency import run_in_threadpool
from typing import Any, Dict, Optional
from api.service import AnalyzeService, get_analyze_service, UploadService, get_upload_service
from entity.dto import UploadDTO
from common.middleware import get_current_user_id, get_current_username
from common.decorators import log, requireInternalToken
from common.utils import success

router: APIRouter = APIRouter(
    prefix="/upload",
    tags=["上传文件接口"],
)

@router.post(
    "",
    summary="上传文件",
    description="上传文件到OSS"
)
@requireInternalToken
@log("上传文件")
async def get_wordcloud(request: Request,data: UploadDTO, analyzeService: AnalyzeService = Depends(get_analyze_service)) -> Any:
    """上传文件接口"""
    
    oss_url: str = await run_in_threadpool(
        analyzeService.upload_file, 
        data.local_file, 
        data.oss_file
    )
    return success(oss_url)

@router.post(
    "/image",
    summary="上传图片",
    description="上传图片到OSS"
)
@log("上传图片")
async def upload_image_to_oss(request: Request, file: UploadFile = File(...), uploadService: UploadService = Depends(get_upload_service)) -> Any:
    """上传图片接口"""
    
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    file_dict: Dict[str, Any] = {
        "filename": file.filename,
        "file": file.file
    }
    result: Dict[str, Any] = await uploadService.handle_image_upload(file_dict)
    return success(result)

@router.post(
    "/pdf",
    summary="上传PDF",
    description="上传PDF到OSS"
)
@log("上传PDF")
async def upload_pdf_to_oss(request: Request, file: UploadFile = File(...), custom_filename: Optional[str] = None, uploadService: UploadService = Depends(get_upload_service)) -> Any:
    """上传PDF接口"""
    
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    file_dict: Dict[str, Any] = {
        "filename": file.filename,
        "file": file.file
    }
    result: Dict[str, Any] = await uploadService.handle_pdf_upload(file_dict, custom_filename)
    return success(result)