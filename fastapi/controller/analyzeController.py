from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from po.listResponse import ListResponse
from service.analyzeService import get_top10_articles_service
from po.article import Article
from config.mysql import SessionLocal,get_db
from service.analyzeService import generate_wordcloud,get_keywords_dic
from utils.response import success

router = APIRouter(
    prefix="/analyze",
    tags=["分析接口"],
)

@router.get("/top10")
def get_top10_articles(db: Session = Depends(get_db)):
    articles = get_top10_articles_service(db)
    return success(ListResponse(total=len(articles), list=articles))

@router.get("/wordcloud")
def get_wordcloud():
    generate_wordcloud(get_keywords_dic())
    return success()