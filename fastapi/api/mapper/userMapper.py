from sqlmodel import Session, select

from entity.po import User

def get_users_by_ids_mapper(user_ids: list[int], db: Session) -> list[User]:
    statement = select(User).where(User.id.in_(user_ids))
    return db.exec(statement).all()

def get_all_users_mapper(db: Session) -> list[User]:
    statement = select(User)
    return db.exec(statement).all()