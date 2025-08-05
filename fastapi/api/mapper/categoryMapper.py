from sqlmodel import Session, select
from entity.po import Category

def get_all_categories_mapper(db: Session) -> list[Category]:
    statement = select(Category).distinct()
    return db.exec(statement).all()