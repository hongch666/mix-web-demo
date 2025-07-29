from fastapi import Depends
from sqlalchemy.orm import Session

from config.mysql import get_db
from entity.po.user import User

def get_users_by_ids_mapper(user_ids: list[int], db: Session) -> list[User]:
    return db.query(User).filter(User.id.in_(user_ids)).all()

def get_all_users_mapper(db: Session) -> list[User]:
    return db.query(User).all()