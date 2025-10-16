from functools import lru_cache
from sqlmodel import Session, select
from entity.po import SubCategory

class SubCategoryMapper:

    def get_all_subcategories_mapper(self, db: Session) -> list[SubCategory]:
        statement = select(SubCategory)
        return db.exec(statement).all()

@lru_cache()
def get_subcategory_mapper() -> SubCategoryMapper:
    return SubCategoryMapper()