from functools import lru_cache
from typing import Any, List, Optional

from app.core.base import Constants
from app.internal.models import User
from sqlalchemy import select
from sqlalchemy.orm import Session


class UserMapper:
    """用户数据访问层 - 数据库查询封装"""

    def get_users_by_ids_mapper(self, user_ids: List[int], db: Session) -> List[User]:
        """根据用户ID列表获取用户列表

        Args:
            user_ids: 用户ID列表
            db: 数据库会话

        Returns:
            用户对象列表
        """
        statement = select(User).where(User.id.in_(user_ids))
        return db.exec(statement).all()

    def get_user_by_id(self, user_id: int, db: Session) -> Optional[User]:
        """根据用户ID获取用户信息

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            用户对象或None
        """
        statement = select(User).where(User.id == user_id)
        return db.exec(statement).first()

    def get_user_role(self, user_id: int, db: Session) -> str:
        """获取用户角色

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            用户角色字符串
        """
        user: Optional[User] = self.get_user_by_id(user_id, db)
        if not user:
            return Constants.ROLE_USER  # 默认返回普通用户角色
        # 如果用户有 role 字段，返回该角色；否则默认返回 'user'
        role: Any = getattr(user, "role", None)
        return role if role else Constants.ROLE_USER


@lru_cache()
def get_user_mapper() -> UserMapper:
    """获取单例 UserMapper 实例

    Returns:
        UserMapper 实例
    """
    return UserMapper()
