from fastapi import APIRouter, Depends, Request
from common.config import get_db
from sqlmodel import Session
from starlette.concurrency import run_in_threadpool
from api.service import AiHistoryService, get_ai_history_service
from common.utils import success
from common.decorators import log, requireInternalToken
from entity.dto import CreateHistoryDTO
from typing import Any

router: APIRouter = APIRouter(
    prefix="/ai_history",
    tags=["AI历史相关接口"],
)

@router.post(
    "",
    summary="创建AI历史记录",
    description="创建一条AI历史记录"
)
@requireInternalToken
@log("创建AI历史记录")
async def create_ai_history(request: Request, data: CreateHistoryDTO, db: Session = Depends(get_db), ai_history_service: AiHistoryService = Depends(get_ai_history_service)) -> Any:
    """创建AI历史记录接口"""
    
    await run_in_threadpool(ai_history_service.create_ai_history, data, db)
    return success()

@router.get(
    "/list",
    summary="获取所有AI历史记录",
    description="获取指定用户的所有AI历史记录"
)
@log("获取所有AI历史记录")
async def get_all_ai_history(request: Request, user_id: int, db: Session = Depends(get_db), ai_history_service: AiHistoryService = Depends(get_ai_history_service)) -> Any:
    """获取所有AI历史记录接口"""
    
    histories = await run_in_threadpool(ai_history_service.get_all_ai_history, user_id, db)
    return success(data=histories)

@router.delete(
    "/{user_id}",
    summary="删除用户所有AI历史记录",
    description="删除指定用户的所有AI历史记录"
)
@log("删除用户所有AI历史记录")
async def delete_ai_history(request: Request, user_id: int, db: Session = Depends(get_db), ai_history_service: AiHistoryService = Depends(get_ai_history_service)) -> Any:
    """删除用户所有AI历史记录接口"""
    
    await run_in_threadpool(ai_history_service.delete_ai_history_by_userid, user_id, db)
    return success()