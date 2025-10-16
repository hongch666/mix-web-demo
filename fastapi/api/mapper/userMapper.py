from functools import lru_cache
from sqlmodel import Session, select
from entity.po import User

class UserMapper:

    def get_users_by_ids_mapper(self,user_ids: list[int], db: Session) -> list[User]:
        statement = select(User).where(User.id.in_(user_ids))
        return db.exec(statement).all()

    def get_all_users_mapper(self,db: Session) -> list[User]:
        statement = select(User)
        return db.exec(statement).all()

@lru_cache()
def get_user_mapper() -> UserMapper:
    return UserMapper()