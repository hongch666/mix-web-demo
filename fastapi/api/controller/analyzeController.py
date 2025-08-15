from fastapi import APIRouter, Depends
from sqlmodel import Session
from api.service import AnalyzeService, get_analyze_service
from common.middleware import get_current_user_id, get_current_username
from entity.po import ListResponse
from config import get_db
from common.utils import success,fileLogger
from starlette.concurrency import run_in_threadpool
from typing import Any, Dict, List

router: APIRouter = APIRouter(
    prefix="/analyze",
    tags=["分析接口"],
)

@router.get("/top10")
async def get_top10_articles(db: Session = Depends(get_db), analyzeService: AnalyzeService = Depends(get_analyze_service)) -> Any:
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    fileLogger.info("用户" + user_id + ":" + username + " GET /analyze/top10: 获取前10篇文章")
    articles: List[Dict[str, Any]] = await run_in_threadpool(analyzeService.get_top10_articles_service, db)
    return success(ListResponse(total=len(articles), list=articles))

@router.post("/wordcloud")
async def get_wordcloud(analyzeService: AnalyzeService = Depends(get_analyze_service)) -> Any:
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    fileLogger.info("用户" + user_id + ":" + username + " POST /analyze/wordcloud: 生成词云图")
    keywords_dic: Dict[str, int] = await run_in_threadpool(analyzeService.get_keywords_dic)
    await run_in_threadpool(analyzeService.generate_wordcloud, keywords_dic)
    oss_url: str = await run_in_threadpool(analyzeService.upload_wordcloud_to_oss)
    return success(oss_url)

@router.post("/excel")
async def get_excel(db: Session = Depends(get_db), analyzeService: AnalyzeService = Depends(get_analyze_service)) -> Any:
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    fileLogger.info("用户" + user_id + ":" + username + " POST /analyze/excel: 获取文章数据Excel")
    await run_in_threadpool(analyzeService.export_articles_to_excel, db)
    oss_url: str = await run_in_threadpool(analyzeService.upload_excel_to_oss)
    return success(oss_url)