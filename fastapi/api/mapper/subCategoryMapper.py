from sqlalchemy.orm import Session

from entity.po import SubCategory

def get_all_subcategories_mapper(db: Session) -> list[SubCategory]:
    return db.query(SubCategory).all()