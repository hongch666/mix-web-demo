from fastapi import APIRouter, Depends, Request
from config import get_db
from sqlmodel import Session
from api.service import AiCommentService, get_ai_comment_service
from common.utils import success
from common.decorators import log
from entity.dto import CreateHistoryDTO
from typing import Any

router: APIRouter = APIRouter(
    prefix="/ai_comment",
    tags=["AI评论相关接口"],
)

@router.post(
    "/{article_id}",
    summary="文章创建AI评论",
    description="为指定文章创建AI评论"
)
@log("文章创建AI评论")
async def create_article_ai_comment(request: Request, article_id: int, db: Session = Depends(get_db), ai_comment_service: AiCommentService = Depends(get_ai_comment_service)) -> Any:
    await ai_comment_service.generate_ai_comments(article_id, db)
    return success();