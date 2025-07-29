from entity.po.category import Category
from sqlalchemy.orm import Session

def get_all_categories_mapper(db: Session) -> list[Category]:
    return db.query(Category).distinct().all()