from fastapi import APIRouter, Depends
from entity.po import ListResponse
from api.service import AnalyzeService, get_analyze_service
from common.utils import success
from common.decorators import log
from starlette.concurrency import run_in_threadpool
from typing import Any, Dict, List

router: APIRouter = APIRouter(
    prefix="/analyze",
    tags=["分析接口"],
)

@router.get("/top10")
@log("获取前10篇文章")
async def get_top10_articles(analyzeService: AnalyzeService = Depends(get_analyze_service)) -> Any:
    articles: List[Dict[str, Any]] = await analyzeService.get_top10_articles_service()
    return success(ListResponse(total=len(articles), list=articles))

@router.post("/wordcloud")
@log("生成词云图")
async def get_wordcloud(analyzeService: AnalyzeService = Depends(get_analyze_service)) -> Any:
    keywords_dic: Dict[str, int] = await analyzeService.get_keywords_dic()
    await run_in_threadpool(analyzeService.generate_wordcloud, keywords_dic)
    oss_url: str = await run_in_threadpool(analyzeService.upload_wordcloud_to_oss)
    return success(oss_url)

@router.post("/excel")
@log("获取文章数据Excel")
async def get_excel(analyzeService: AnalyzeService = Depends(get_analyze_service)) -> Any:
    await analyzeService.export_articles_to_excel()
    oss_url: str = await run_in_threadpool(analyzeService.upload_excel_to_oss)
    return success(oss_url)