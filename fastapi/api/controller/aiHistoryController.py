from fastapi import APIRouter, Depends, Request
from config import get_db
from sqlmodel import Session
from api.service import AiHistoryService, get_ai_history_service
from common.utils import success
from common.decorators import log

from entity.dto import CreateHistoryDTO
from typing import Any

router: APIRouter = APIRouter(
    prefix="/ai_history",
    tags=["AI历史相关接口"],
)

@router.post("")
@log("创建AI历史记录")
def create_ai_history(request: Request, data: CreateHistoryDTO, db: Session = Depends(get_db),ai_history_service: AiHistoryService = Depends(get_ai_history_service)) -> Any:
    ai_history_service.create_ai_history(data, db)
    return success();

@router.get("")
@log("获取所有AI历史记录")
def get_all_ai_history(request: Request, user_id: int, db: Session = Depends(get_db), ai_history_service: AiHistoryService = Depends(get_ai_history_service)) -> Any:
    histories = ai_history_service.get_all_ai_history(user_id, db)
    return success(data=histories);