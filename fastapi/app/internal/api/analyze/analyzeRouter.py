from typing import Any

from fastapi import APIRouter, Request

from app.core.base import ApiResponse, ListResponse, success
from app.core.constants import SwaggerConfig
from app.core.decorators import log, requireAdmin, requireInternalToken
from app.dependencies import AnalyzeServiceDep, DbSession
from app.internal.schemas import (
    ArticleStatisticsResponse,
    CategoryArticleCountResponse,
    MonthlyPublishCountResponse,
)

router: APIRouter = APIRouter(
    prefix="/analyze",
    tags=["文章分析模块"],
)


@router.get(
    "/top10",
    summary="获取前10篇文章",
    description="获取阅读量前10的文章",
    response_model=ApiResponse[ListResponse[dict[str, Any]]],
    responses=SwaggerConfig.REMOTE_FAILURE_RESPONSES,
)
@log("获取前10篇文章")
async def get_top10_articles(
    request: Request,
    db: DbSession,
    analyzeService: AnalyzeServiceDep,
) -> ApiResponse:
    """获取前10篇文章接口"""

    articles: list[dict[str, Any]] = await analyzeService.get_top10_articles_service_sf(
        db
    )
    return success(ListResponse(total=len(articles), list=articles))


@router.post(
    "/wordcloud",
    summary="生成词云图",
    description="根据文章生成词云图（支持Redis缓存，24h过期）",
    response_model=ApiResponse[str],
    responses=SwaggerConfig.REMOTE_FAILURE_RESPONSES,
)
@log("生成词云图")
async def get_wordcloud(
    request: Request, analyzeService: AnalyzeServiceDep
) -> ApiResponse:
    """生成词云图接口"""

    oss_url: str = await analyzeService.get_wordcloud_service_sf()
    return success(oss_url)


@router.get(
    "/internal/wordcloud-url",
    summary="查询当前词云 OSS 链接（内部）",
    description="只读返回当前缓存中的词云链接，缓存过期返回 null 且不重新生成，供 OSS 清理任务判断在用引用",
)
@requireInternalToken
async def get_current_wordcloud_url(
    request: Request, analyzeService: AnalyzeServiceDep
) -> ApiResponse:
    """查询当前词云 OSS 链接供清理任务排除，不触发生成"""
    url: str | None = await analyzeService.get_current_wordcloud_url()
    return success(url)


@router.post(
    "/excel",
    summary="获取文章数据Excel",
    description="导出文章数据到Excel并上传到OSS",
    response_model=ApiResponse[str],
    responses={
        **SwaggerConfig.FORBIDDEN_RESPONSE,
        **SwaggerConfig.REMOTE_FAILURE_RESPONSES,
    },
)
@requireAdmin
@log("获取文章数据Excel")
async def get_excel(
    request: Request,
    db: DbSession,
    analyzeService: AnalyzeServiceDep,
) -> ApiResponse:
    """获取文章数据Excel接口"""

    oss_url: str = await analyzeService.export_and_upload_articles_excel(db)
    return success(oss_url)


@router.get(
    "/statistics",
    summary="获取文章统计信息",
    description="返回平台文章的阅读量、文章数、活跃作者数、点赞与收藏的汇总值及平均值",
    response_model=ApiResponse[ArticleStatisticsResponse],
    responses=SwaggerConfig.REMOTE_FAILURE_RESPONSES,
)
@log("获取文章统计信息")
async def get_article_statistics(
    request: Request,
    db: DbSession,
    analyzeService: AnalyzeServiceDep,
) -> ApiResponse:
    """获取文章统计信息"""

    result: dict[str, Any] = await analyzeService.get_article_statistics_service_sf(db)
    return success(result)


@router.get(
    "/article-count-by-category",
    summary="按分类统计文章数量",
    description="获取所有大分类的文章数量分布，包括没有文章的分类",
    response_model=ApiResponse[ListResponse[CategoryArticleCountResponse]],
    responses=SwaggerConfig.REMOTE_FAILURE_RESPONSES,
)
@log("按分类统计文章数量")
async def get_article_count_by_category(
    request: Request,
    db: DbSession,
    analyzeService: AnalyzeServiceDep,
) -> ApiResponse:
    """按大分类统计文章数量"""

    result: list[
        dict[str, Any]
    ] = await analyzeService.get_category_article_count_service_sf(db)
    return success(ListResponse(total=len(result), list=result))


@router.get(
    "/monthly-publish-count",
    summary="获取月度文章发布统计",
    description="获取全部月份的文章发布数量统计（从最早有数据的月份到当前月，缺失月份置为0）",
    response_model=ApiResponse[ListResponse[MonthlyPublishCountResponse]],
    responses=SwaggerConfig.REMOTE_FAILURE_RESPONSES,
)
@log("获取月度文章发布统计")
async def get_monthly_publish_count(
    request: Request,
    db: DbSession,
    analyzeService: AnalyzeServiceDep,
) -> ApiResponse:
    """获取月度文章发布统计"""

    result: list[
        dict[str, Any]
    ] = await analyzeService.get_monthly_publish_count_service_sf(db)
    return success(ListResponse(total=len(result), list=result))
