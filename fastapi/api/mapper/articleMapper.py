from fastapi import Depends
from sqlalchemy.orm import Session

from config import get_db
from entity.po import Article

def get_top10_articles_mapper(db: Session) -> list[Article]:
    return db.query(Article).limit(10).all()

def get_all_articles_mapper(db: Session) -> list[Article]:
    return db.query(Article).all()

def get_article_limit_mapper(db: Session) -> list[Article]:
    return db.query(Article).order_by(Article.create_at.desc()).limit(100).all()