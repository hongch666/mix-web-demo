from sqlmodel import Session, select

from config import get_db
from entity.po import Article

def get_top10_articles_mapper(db: Session) -> list[Article]:
    statement = select(Article).order_by(Article.views.desc()).limit(10)
    return db.exec(statement).all()

def get_all_articles_mapper(db: Session) -> list[Article]:
    statement = select(Article)
    return db.exec(statement).all()

def get_article_limit_mapper(db: Session) -> list[Article]:
    statement = select(Article).order_by(Article.create_at.desc()).limit(100)
    return db.exec(statement).all()