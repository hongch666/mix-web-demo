from typing import Any, Dict, List

from app.common.decorators import log, requireAdmin
from app.core.base import ApiResponse, success
from app.dependencies import AnalyzeServiceDep, DbSession
from app.internal.schemas import ListResponse

from fastapi import APIRouter, Request

router: APIRouter = APIRouter(
    prefix="/analyze",
    tags=["文章分析模块"],
)


@router.get(
    "/top10",
    summary="获取前10篇文章",
    description="获取阅读量前10的文章",
    response_model=ApiResponse,
)
@log("获取前10篇文章")
async def get_top10_articles(
    request: Request,
    db: DbSession,
    analyzeService: AnalyzeServiceDep,
) -> ApiResponse:
    """获取前10篇文章接口"""

    articles: List[Dict[str, Any]] = await analyzeService.get_top10_articles_service_sf(
        db
    )
    return success(ListResponse(total=len(articles), list=articles))


@router.post(
    "/wordcloud",
    summary="生成词云图",
    description="根据文章生成词云图（支持Redis缓存，24h过期）",
    response_model=ApiResponse,
)
@log("生成词云图")
async def get_wordcloud(
    request: Request, analyzeService: AnalyzeServiceDep
) -> ApiResponse:
    """生成词云图接口"""

    oss_url: str = await analyzeService.get_wordcloud_service_sf()
    return success(oss_url)


@router.post(
    "/excel",
    summary="获取文章数据Excel",
    description="导出文章数据到Excel并上传到OSS",
    response_model=ApiResponse,
)
@requireAdmin
@log("获取文章数据Excel")
async def get_excel(
    request: Request,
    db: DbSession,
    analyzeService: AnalyzeServiceDep,
) -> ApiResponse:
    """获取文章数据Excel接口"""

    file_path: str = await analyzeService.export_articles_to_excel(db)
    oss_url: str = await analyzeService.upload_excel_to_oss(file_path)
    return success(oss_url)


@router.get(
    "/statistics",
    summary="获取文章统计信息",
    description="获取文章统计信息",
    response_model=ApiResponse,
)
@log("获取文章统计信息")
async def get_article_statistics(
    request: Request,
    db: DbSession,
    analyzeService: AnalyzeServiceDep,
) -> ApiResponse:
    """获取文章统计信息"""

    result: Dict[str, Any] = await analyzeService.get_article_statistics_service_sf(db)
    return success(result)


@router.get(
    "/article-count-by-category",
    summary="按分类统计文章数量",
    description="获取所有大分类的文章数量分布，包括没有文章的分类",
    response_model=ApiResponse,
)
@log("按分类统计文章数量")
async def get_article_count_by_category(
    request: Request,
    db: DbSession,
    analyzeService: AnalyzeServiceDep,
) -> ApiResponse:
    """按大分类统计文章数量"""

    result: List[
        Dict[str, Any]
    ] = await analyzeService.get_category_article_count_service_sf(db)
    return success(ListResponse(total=len(result), list=result))


@router.get(
    "/monthly-publish-count",
    summary="获取月度文章发布统计",
    description="获取最近6个月的文章发布数量统计（从当前月向前推6个月，缺失月份置为0）",
    response_model=ApiResponse,
)
@log("获取月度文章发布统计")
async def get_monthly_publish_count(
    request: Request,
    db: DbSession,
    analyzeService: AnalyzeServiceDep,
) -> ApiResponse:
    """获取月度文章发布统计"""

    result: List[
        Dict[str, Any]
    ] = await analyzeService.get_monthly_publish_count_service_sf(db)
    return success(ListResponse(total=len(result), list=result))
