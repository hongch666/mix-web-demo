from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from po.listResponse import ListResponse
from service.analyzeService import get_top10_articles_service
from config.mysql import get_db
from service.analyzeService import generate_wordcloud,get_keywords_dic,upload_wordcloud_to_oss
from utils.response import success
from utils.logger import logger
from starlette.concurrency import run_in_threadpool

router = APIRouter(
    prefix="/analyze",
    tags=["分析接口"],
)

@router.get("/top10")
async def get_top10_articles(db: Session = Depends(get_db)):
    logger.info("GET /analyze/top10: 获取前10篇文章")
    articles = await run_in_threadpool(get_top10_articles_service,db)
    return success(ListResponse(total=len(articles), list=articles))

@router.post("/wordcloud")
async def get_wordcloud():
    logger.info("POST /analyze/wordcloud: 生成词云图")
    keywords_dic = await run_in_threadpool(get_keywords_dic)
    await run_in_threadpool(generate_wordcloud, keywords_dic)
    oss_url = await run_in_threadpool(upload_wordcloud_to_oss)
    return success(oss_url)
