from typing import Any

from app.common.decorators import log
from app.core.base import Constants, success
from app.core.db import get_db
from app.internal.crud import (
    ArticleMapper,
    CommentsMapper,
    get_article_mapper,
    get_comments_mapper,
)
from app.internal.schemas import GenerateDTO
from app.internal.services import (
    DeepseekService,
    GeminiService,
    GenerateService,
    GptService,
    get_deepseek_service,
    get_gemini_service,
    get_generate_service,
    get_gpt_service,
)
from sqlalchemy.orm import Session

from fastapi import APIRouter, BackgroundTasks, Depends, Request

router: APIRouter = APIRouter(
    prefix="/generate",
    tags=["生成相关接口"],
)


@router.post("/tags", summary="生成tags", description="根据输入文本生成tags数组")
@log("生成tags")
async def generate_tags(
    request: Request,
    data: GenerateDTO,
    generateService: GenerateService = Depends(get_generate_service),
) -> Any:
    """生成tags接口"""

    tags: list[str] = await generateService.extract_tags(data.text)
    return success(tags)


@router.post(
    "/ai_comment/{article_id}",
    summary="文章创建AI评论",
    description="为指定文章创建AI评论",
)
@log("文章创建AI评论")
async def create_article_ai_comment(
    request: Request,
    article_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    comments_mapper: CommentsMapper = Depends(get_comments_mapper),
    article_mapper: ArticleMapper = Depends(get_article_mapper),
    deepseek_service: DeepseekService = Depends(get_deepseek_service),
    gemini_service: GeminiService = Depends(get_gemini_service),
    gpt_service: GptService = Depends(get_gpt_service),
) -> Any:
    """文章创建AI评论接口"""

    # 创建完整的 GenerateService 实例
    generate_service = GenerateService(
        comments_mapper=comments_mapper,
        article_mapper=article_mapper,
        deepseek_service=deepseek_service,
        gemini_service=gemini_service,
        gpt_service=gpt_service,
    )
    # 添加后台任务
    background_tasks.add_task(generate_service.generate_ai_comments, article_id, db)
    return success(
        data={"message": Constants.AI_COMMENT_TASK_SUBMITTED, "article_id": article_id}
    )


@router.post(
    "/ai_comment_with_reference/{article_id}",
    summary="文章创建基于权威参考文本的AI评论",
    description="为指定文章创建基于权威参考文本的AI评论，使用权威参考文本进行评价打分",
)
@log("文章创建基于权威参考文本的AI评论")
async def create_article_ai_comment_with_reference(
    request: Request,
    article_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    comments_mapper: CommentsMapper = Depends(get_comments_mapper),
    article_mapper: ArticleMapper = Depends(get_article_mapper),
    deepseek_service: DeepseekService = Depends(get_deepseek_service),
    gemini_service: GeminiService = Depends(get_gemini_service),
    gpt_service: GptService = Depends(get_gpt_service),
) -> Any:
    """文章创建基于权威参考文本的AI评论接口"""

    # 创建完整的 GenerateService 实例
    generate_service = GenerateService(
        comments_mapper=comments_mapper,
        article_mapper=article_mapper,
        deepseek_service=deepseek_service,
        gemini_service=gemini_service,
        gpt_service=gpt_service,
    )
    # 添加后台任务
    background_tasks.add_task(
        generate_service.generate_ai_comments_with_reference, article_id, db
    )
    return success(
        data={
            "message": Constants.AI_COMMENT_WITH_REFERENCE_TASK_SUBMITTED,
            "article_id": article_id,
        }
    )
