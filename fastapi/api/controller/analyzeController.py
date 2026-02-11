from fastapi import APIRouter, Depends, Request
from sqlmodel import Session
from starlette.concurrency import run_in_threadpool
from typing import Any, Dict, List
from api.service import AnalyzeService, get_analyze_service
from entity.po import ListResponse
from common.config import get_db
from common.utils import success
from common.decorators import log, requireInternalToken, requireAdmin

router: APIRouter = APIRouter(
    prefix="/analyze",
    tags=["文章分析接口"],
)

@router.get(
    "/top10",
    summary="获取前10篇文章",
    description="获取阅读量前10的文章"
)
@log("获取前10篇文章")
async def get_top10_articles(
    _: Request, 
    db: Session = Depends(get_db), 
    analyzeService: AnalyzeService = Depends(get_analyze_service)
) -> Any:
    """获取前10篇文章接口"""
    
    articles: List[Dict[str, Any]] = await run_in_threadpool(analyzeService.get_top10_articles_service, db)
    return success(ListResponse(total=len(articles), list=articles))

@router.post(
    "/wordcloud",
    summary="生成词云图",
    description="根据文章生成词云图（支持Redis缓存，24h过期）"
)
@log("生成词云图")
async def get_wordcloud(
    _: Request,
    analyzeService: AnalyzeService = Depends(get_analyze_service)
) -> Any:
    """生成词云图接口"""
    
    oss_url: str = await run_in_threadpool(analyzeService.get_wordcloud_service)
    return success(oss_url)

@router.post(
    "/excel",
    summary="获取文章数据Excel",
    description="导出文章数据到Excel并上传到OSS"
)
@requireAdmin
@requireInternalToken
@log("获取文章数据Excel")
async def get_excel(
    _: Request, 
    db: Session = Depends(get_db), 
    analyzeService: AnalyzeService = Depends(get_analyze_service)
) -> Any:
    """获取文章数据Excel接口"""
    
    await run_in_threadpool(analyzeService.export_articles_to_excel, db)
    oss_url: str = await run_in_threadpool(analyzeService.upload_excel_to_oss)
    return success(oss_url)

@router.get(
    "/statistics",
    summary="获取文章统计信息",
    description="获取文章统计信息"
)
@log("获取文章统计信息")
async def get_article_statistics(
    _: Request, 
    db: Session = Depends(get_db), 
    analyzeService: AnalyzeService = Depends(get_analyze_service)
) -> Any:
    """获取文章统计信息"""
    
    result: Dict[str, Any] = await run_in_threadpool(analyzeService.get_article_statistics_service, db)
    return success(result)

@router.get(
    "/article-count-by-category",
    summary="按分类统计文章数量",
    description="获取所有大分类的文章数量分布，包括没有文章的分类"
)
@log("按分类统计文章数量")
async def get_article_count_by_category(
    _: Request, 
    db: Session = Depends(get_db), 
    analyzeService: AnalyzeService = Depends(get_analyze_service)
) -> Any:
    """按大分类统计文章数量"""
    
    result: List[Dict[str, Any]] = await run_in_threadpool(analyzeService.get_category_article_count_service, db)
    return success(ListResponse(total=len(result), list=result))

@router.get(
    "/monthly-publish-count",
    summary="获取月度文章发布统计",
    description="获取最近6个月的文章发布数量统计（从当前月向前推6个月，缺失月份置为0）"
)
@log("获取月度文章发布统计")
async def get_monthly_publish_count(
    _: Request, 
    db: Session = Depends(get_db), 
    analyzeService: AnalyzeService = Depends(get_analyze_service)
) -> Any:
    """获取月度文章发布统计"""
    
    result: List[Dict[str, Any]] = await run_in_threadpool(analyzeService.get_monthly_publish_count_service, db)
    return success(ListResponse(total=len(result), list=result))
