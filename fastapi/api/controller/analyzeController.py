from fastapi import APIRouter, Depends
from sqlmodel import Session
from common.middleware import get_current_user_id, get_current_username
from entity.po import ListResponse
from api.service import get_top10_articles_service, upload_excel_to_oss,generate_wordcloud, get_keywords_dic, upload_wordcloud_to_oss, export_articles_to_excel
from common.utils import success,fileLogger
from starlette.concurrency import run_in_threadpool
from typing import Any, Dict, List

router: APIRouter = APIRouter(
    prefix="/analyze",
    tags=["分析接口"],
)

@router.get("/top10")
async def get_top10_articles() -> Any:
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    fileLogger.info("用户" + user_id + ":" + username + " GET /analyze/top10: 获取前10篇文章")
    articles: List[Dict[str, Any]] = await get_top10_articles_service()
    return success(ListResponse(total=len(articles), list=articles))

@router.post("/wordcloud")
async def get_wordcloud() -> Any:
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    fileLogger.info("用户" + user_id + ":" + username + " POST /analyze/wordcloud: 生成词云图")
    keywords_dic: Dict[str, int] = await get_keywords_dic()
    await run_in_threadpool(generate_wordcloud, keywords_dic)
    oss_url: str = await run_in_threadpool(upload_wordcloud_to_oss)
    return success(oss_url)

@router.post("/excel")
async def get_excel() -> Any:
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    fileLogger.info("用户" + user_id + ":" + username + " POST /analyze/excel: 获取文章数据Excel")
    await export_articles_to_excel()
    oss_url: str = await run_in_threadpool(upload_excel_to_oss)
    return success(oss_url)