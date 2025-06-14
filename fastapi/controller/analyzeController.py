from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from po.listResponse import ListResponse
from service.analyzeService import get_top10_articles_service
from config.mysql import get_db
from service.analyzeService import generate_wordcloud,get_keywords_dic,upload_wordcloud_to_oss
from utils.response import success
from starlette.concurrency import run_in_threadpool

router = APIRouter(
    prefix="/analyze",
    tags=["分析接口"],
)

@router.get("/top10")
async def get_top10_articles(db: Session = Depends(get_db)):
    articles = await run_in_threadpool(get_top10_articles_service,db)
    return success(ListResponse(total=len(articles), list=articles))

@router.post("/wordcloud")
async def get_wordcloud():
    keywords_dic = await run_in_threadpool(get_keywords_dic)
    await run_in_threadpool(generate_wordcloud, keywords_dic)
    oss_url = await run_in_threadpool(upload_wordcloud_to_oss)
    return success(oss_url)
