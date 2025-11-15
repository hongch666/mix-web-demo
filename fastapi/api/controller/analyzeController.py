from fastapi import APIRouter, Depends, Request
from sqlmodel import Session
from starlette.concurrency import run_in_threadpool
from typing import Any, Dict, List
from api.service import AnalyzeService, get_analyze_service, get_apilog_service, ApiLogService
from entity.po import ListResponse
from config import get_db
from common.utils import success
from common.decorators import log

router: APIRouter = APIRouter(
    prefix="/analyze",
    tags=["分析接口"],
)

@router.get(
    "/top10",
    summary="获取前10篇文章",
    description="获取阅读量前10的文章"
)
@log("获取前10篇文章")
async def get_top10_articles(request: Request, db: Session = Depends(get_db), analyzeService: AnalyzeService = Depends(get_analyze_service)) -> Any:
    articles: List[Dict[str, Any]] = await run_in_threadpool(analyzeService.get_top10_articles_service, db)
    return success(ListResponse(total=len(articles), list=articles))

@router.post(
    "/wordcloud",
    summary="生成词云图",
    description="根据文章生成词云图"
)
@log("生成词云图")
async def get_wordcloud(request: Request,analyzeService: AnalyzeService = Depends(get_analyze_service)) -> Any:
    keywords_dic: Dict[str, int] = await run_in_threadpool(analyzeService.get_keywords_dic)
    await run_in_threadpool(analyzeService.generate_wordcloud, keywords_dic)
    oss_url: str = await run_in_threadpool(analyzeService.upload_wordcloud_to_oss)
    return success(oss_url)

@router.post(
    "/excel",
    summary="获取文章数据Excel",
    description="导出文章数据到Excel并上传到OSS"
)
@log("获取文章数据Excel")
async def get_excel(request: Request, db: Session = Depends(get_db), analyzeService: AnalyzeService = Depends(get_analyze_service)) -> Any:
    await run_in_threadpool(analyzeService.export_articles_to_excel, db)
    oss_url: str = await run_in_threadpool(analyzeService.upload_excel_to_oss)
    return success(oss_url)

@router.get(
    "/api/average-speed",
    summary="获取所有接口的平均响应速度",
    description="获取所有接口的平均响应速度"
)
@log("获取所有接口的平均响应速度")
async def get_api_average_speed(request: Request, apilogService: ApiLogService = Depends(get_apilog_service)) -> Any:
    """
    获取所有接口的平均响应速度
    按照接口路径和方法分组统计
    """
    result: List[Dict[str, Any]] = await run_in_threadpool(apilogService.get_api_average_response_time_service)
    return success(result)

@router.get(
    "/api/called-count",
    summary="获取接口调用次数",
    description="获取接口调用次数"
)
@log("获取接口调用次数")
async def get_called_count_apis(request: Request, apilogService: ApiLogService = Depends(get_apilog_service)) -> Any:
    """
    获取接口调用次数
    按照接口路径和方法分组统计
    """
    result: List[Dict[str, Any]] = await run_in_threadpool(apilogService.get_called_count_apis_service)
    return success(result)

@router.get(
    "/statistics",
    summary="获取文章统计信息",
    description="获取文章统计信息"
)
@log("获取文章统计信息")
async def get_article_statistics(request: Request, db: Session = Depends(get_db), analyzeService: AnalyzeService = Depends(get_analyze_service)) -> Any:
    """
    获取文章统计信息
    返回：总阅读量、文章总数、活跃作者数（所有有文章的用户）、平均阅读次数
    """
    result: Dict[str, Any] = await run_in_threadpool(analyzeService.get_article_statistics_service, db)
    return success(result)

@router.get(
    "/article-count-by-category",
    summary="按分类统计文章数量",
    description="获取所有大分类的文章数量分布，包括没有文章的分类"
)
@log("按分类统计文章数量")
async def get_article_count_by_category(request: Request, db: Session = Depends(get_db), analyzeService: AnalyzeService = Depends(get_analyze_service)) -> Any:
    """
    按大分类统计文章数量
    
    特点:
    - 返回所有大分类（包括没有文章的分类，返回0）
    - 按文章数量从多到少排序
    - 使用Hive查询+缓存优化，支持降级处理（Spark → DB）
    """
    result: List[Dict[str, Any]] = await run_in_threadpool(analyzeService.get_category_article_count_service, db)
    return success(ListResponse(total=len(result), list=result))

@router.get(
    "/monthly-publish-count",
    summary="获取月度文章发布统计",
    description="获取最近24个月的文章发布数量统计（从当前月向前推24个月，缺失月份置为0）"
)
@log("获取月度文章发布统计")
async def get_monthly_publish_count(request: Request, db: Session = Depends(get_db), analyzeService: AnalyzeService = Depends(get_analyze_service)) -> Any:
    """
    获取月度文章发布统计
    
    特性：
    - 从当前月份向前推24个月
    - 中间缺失的月份自动补零
    - 按月份倒序排列（最新在前）
    """
    result: List[Dict[str, Any]] = await run_in_threadpool(analyzeService.get_monthly_publish_count_service, db)
    return success(ListResponse(total=len(result), list=result))
