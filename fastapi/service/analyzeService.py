from sqlalchemy.orm import Session
from fastapi import Depends

from config.mysql import get_db
from po.article import Article

def get_top10_articles_service(db: Session = Depends(get_db)):
    articles = db.query(Article).order_by(Article.views.desc()).limit(10).all()
    return articles