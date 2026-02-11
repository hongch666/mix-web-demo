from functools import lru_cache
from typing import List, Optional
from sqlmodel import Session, select
from entity.po import User

class UserMapper:
    """用户 Mapper"""

    def get_users_by_ids_mapper(self, user_ids: List[int], db: Session) -> List[User]:
        statement = select(User).where(User.id.in_(user_ids))
        return db.exec(statement).all()

    def get_user_by_id(self, user_id: int, db: Session) -> Optional[User]:
        """获取用户信息"""
        statement = select(User).where(User.id == user_id)
        return db.exec(statement).first()

    def get_user_role(self, user_id: int, db: Session) -> str:
        """获取用户角色"""
        user = self.get_user_by_id(user_id, db)
        if not user:
            return "user"  # 默认返回普通用户角色
        # 如果用户有 role 字段，返回该角色；否则默认返回 'user'
        role = getattr(user, 'role', None)
        return role if role else "user"

@lru_cache()
def get_user_mapper() -> UserMapper:
    return UserMapper()