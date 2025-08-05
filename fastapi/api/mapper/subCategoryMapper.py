from sqlmodel import Session, select

from entity.po import SubCategory

def get_all_subcategories_mapper(db: Session) -> list[SubCategory]:
    statement = select(SubCategory)
    return db.exec(statement).all()