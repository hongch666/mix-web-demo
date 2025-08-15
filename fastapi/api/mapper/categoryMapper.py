from functools import lru_cache
from sqlmodel import Session, select
from entity.po import Category

class CategoryMapper:

    def get_all_categories_mapper(self, db: Session) -> list[Category]:
        statement = select(Category).distinct()
        return db.exec(statement).all()
    
@lru_cache()
def get_category_mapper() -> CategoryMapper:
    return CategoryMapper()