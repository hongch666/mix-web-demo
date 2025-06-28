from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from common.middleware.ContextMiddleware import get_current_user_id, get_current_username
from entity.po.listResponse import ListResponse
from api.service.analyzeService import get_top10_articles_service
from config.mysql import get_db
from api.service.analyzeService import generate_wordcloud, get_keywords_dic, upload_wordcloud_to_oss
from common.utils.response import success
from common.utils.writeLog import fileLogger
from starlette.concurrency import run_in_threadpool
from typing import Any, Dict, List

router: APIRouter = APIRouter(
    prefix="/analyze",
    tags=["分析接口"],
)

@router.get("/top10")
async def get_top10_articles(db: Session = Depends(get_db)) -> Any:
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    fileLogger.info("用户" + user_id + ":" + username + " GET /analyze/top10: 获取前10篇文章")
    articles: List[Dict[str, Any]] = await run_in_threadpool(get_top10_articles_service, db)
    return success(ListResponse(total=len(articles), list=articles))

@router.post("/wordcloud")
async def get_wordcloud() -> Any:
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    fileLogger.info("用户" + user_id + ":" + username + " POST /analyze/wordcloud: 生成词云图")
    keywords_dic: Dict[str, int] = await run_in_threadpool(get_keywords_dic)
    await run_in_threadpool(generate_wordcloud, keywords_dic)
    oss_url: str = await run_in_threadpool(upload_wordcloud_to_oss)
    return success(oss_url)
