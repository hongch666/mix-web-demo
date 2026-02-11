from fastapi import APIRouter, Depends, Request, BackgroundTasks
from typing import Any
from starlette.concurrency import run_in_threadpool
from common.config import get_db
from sqlmodel import Session
from api.service import (
    GenerateService, get_generate_service,
    DoubaoService, get_doubao_service, 
    GeminiService, get_gemini_service, 
    QwenService, get_qwen_service
)
from api.mapper import (
    CommentsMapper, get_comments_mapper, 
    ArticleMapper, get_article_mapper
)
from common.utils import success
from common.decorators import log
from common.utils import Constants
from entity.dto import GenerateDTO

router: APIRouter = APIRouter(
    prefix="/generate",
    tags=["生成相关接口"],
)

@router.post(
    "/tags",
    summary="生成tags",
    description="根据输入文本生成tags数组"
)
@log("生成tags")
async def generate_tags(
    _: Request, 
    data: GenerateDTO, 
    generateService: GenerateService = Depends(get_generate_service)
) -> Any:
    """生成tags接口"""
    
    tags: list[str] = await run_in_threadpool(
        generateService.extract_tags,
        data.text,
    )
    return success(tags)

@router.post(
    "/ai_comment/{article_id}",
    summary="文章创建AI评论",
    description="为指定文章创建AI评论"
)
@log("文章创建AI评论")
async def create_article_ai_comment(
    _: Request, 
    article_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    comments_mapper: CommentsMapper = Depends(get_comments_mapper),
    article_mapper: ArticleMapper = Depends(get_article_mapper),
    doubao_service: DoubaoService = Depends(get_doubao_service),
    gemini_service: GeminiService = Depends(get_gemini_service),
    qwen_service: QwenService = Depends(get_qwen_service)
) -> Any:
    """文章创建AI评论接口"""
    
    # 创建完整的 GenerateService 实例
    generate_service = GenerateService(
        comments_mapper=comments_mapper,
        article_mapper=article_mapper,
        doubao_service=doubao_service,
        gemini_service=gemini_service,
        qwen_service=qwen_service
    )
    # 添加后台任务
    background_tasks.add_task(generate_service.generate_ai_comments, article_id, db)
    return success(data={"message": Constants.AI_COMMENT_TASK_SUBMITTED, "article_id": article_id})

@router.post(
    "/ai_comment_with_reference/{article_id}",
    summary="文章创建基于权威参考文本的AI评论",
    description="为指定文章创建基于权威参考文本的AI评论，使用权威参考文本进行评价打分"
)
@log("文章创建基于权威参考文本的AI评论")
async def create_article_ai_comment_with_reference(
    _: Request, 
    article_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    comments_mapper: CommentsMapper = Depends(get_comments_mapper),
    article_mapper: ArticleMapper = Depends(get_article_mapper),
    doubao_service: DoubaoService = Depends(get_doubao_service),
    gemini_service: GeminiService = Depends(get_gemini_service),
    qwen_service: QwenService = Depends(get_qwen_service)
) -> Any:
    """文章创建基于权威参考文本的AI评论接口"""
    
    # 创建完整的 GenerateService 实例
    generate_service = GenerateService(
        comments_mapper=comments_mapper,
        article_mapper=article_mapper,
        doubao_service=doubao_service,
        gemini_service=gemini_service,
        qwen_service=qwen_service
    )
    # 添加后台任务
    background_tasks.add_task(generate_service.generate_ai_comments_with_reference, article_id, db)
    return success(data={"message": Constants.AI_COMMENT_WITH_REFERENCE_TASK_SUBMITTED, "article_id": article_id})