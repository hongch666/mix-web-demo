from app.common.decorators import log
from app.core.base import success
from app.core.base.response import ApiResponse
from app.core.constants import Messages
from app.dependencies import (
    DbSession,
    GenerateServiceDep,
)
from app.internal.schemas import GenerateDTO

from fastapi import APIRouter, BackgroundTasks, Path, Request

router: APIRouter = APIRouter(
    prefix="/generate",
    tags=["生成模块"],
)


@router.post(
    "/tags",
    summary="生成tags",
    description="根据输入文本生成tags数组",
    response_model=ApiResponse,
)
@log("生成tags")
async def generate_tags(
    request: Request,
    data: GenerateDTO,
    generateService: GenerateServiceDep,
) -> ApiResponse:
    """生成tags接口"""

    tags: list[str] = await generateService.extract_tags(data.text)
    return success(tags)


@router.post(
    "/ai_comment/{article_id}",
    summary="文章创建AI评论",
    description="为指定文章创建AI评论",
    response_model=ApiResponse,
)
@log("文章创建AI评论")
async def create_article_ai_comment(
    request: Request,
    background_tasks: BackgroundTasks,
    db: DbSession,
    generate_service: GenerateServiceDep,
    articleId: int = Path(alias="article_id"),
) -> ApiResponse:
    """文章创建AI评论接口"""

    # 添加后台任务
    background_tasks.add_task(generate_service.generate_ai_comments, articleId, db)
    return success(
        data={"message": Messages.AI_COMMENT_TASK_SUBMITTED, "article_id": articleId}
    )


@router.post(
    "/ai_comment_with_reference/{article_id}",
    summary="文章创建基于权威参考文本的AI评论",
    description="为指定文章创建基于权威参考文本的AI评论，使用权威参考文本进行评价打分",
    response_model=ApiResponse,
)
@log("文章创建基于权威参考文本的AI评论")
async def create_article_ai_comment_with_reference(
    request: Request,
    background_tasks: BackgroundTasks,
    db: DbSession,
    generate_service: GenerateServiceDep,
    articleId: int = Path(alias="article_id"),
) -> ApiResponse:
    """文章创建基于权威参考文本的AI评论接口"""

    # 添加后台任务
    background_tasks.add_task(
        generate_service.generate_ai_comments_with_reference, articleId, db
    )
    return success(
        data={
            "message": Messages.AI_COMMENT_WITH_REFERENCE_TASK_SUBMITTED,
            "article_id": articleId,
        }
    )
