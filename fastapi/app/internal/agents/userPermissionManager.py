from functools import lru_cache
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.base import Logger
from app.core.constants import Messages
from app.internal.agents.toolScope import clear_tool_scope, set_tool_scope
from app.internal.clients import SpringClient, get_spring_client


class UserPermissionManager:
    """用户权限管理器"""

    def __init__(
        self,
        user_mapper: Optional[Any] = None,
        spring_client: Optional[SpringClient] = None,
    ) -> None:
        """
        初始化权限管理器

        Args:
            user_mapper: 用户 Mapper 实例
            spring_client: Spring 客户端实例，缺省取共享单例
        """
        self.user_mapper: Optional[Any] = user_mapper
        self._spring_client: SpringClient = spring_client or get_spring_client()

    async def get_user_role_async(self, user_id: int, db: Session) -> Optional[str]:
        """异步获取用户角色"""
        try:
            # 使用SpringClient远程获取用户信息
            users = await self._spring_client.get_users_by_ids([user_id])
            if not users:
                Logger.warning(Messages.USER_ROLE_MAPPER_UNINITIALIZED(user_id))
                return Messages.ROLE_USER

            user_data = users[0]
            role: Optional[str] = user_data.get("role") or Messages.ROLE_USER
            Logger.info(Messages.USER_ROLE_LOADED(user_id, role))
            return role
        except Exception as e:
            Logger.error(Messages.USER_ROLE_LOAD_FAILED(user_id, e))
            return Messages.ROLE_USER

    async def is_admin_async(self, user_id: int, db: Session) -> bool:
        role: Optional[str] = await self.get_user_role_async(user_id, db)
        return role == Messages.ROLE_ADMIN

    def apply_tool_scope(self, user_id: int, role: Optional[str]) -> None:
        """写入当前请求的工具作用域：admin 不限行范围，其他用户限定本人数据"""
        set_tool_scope(user_id, role == Messages.ROLE_ADMIN)

    async def can_access_sql_tools_async(
        self, user_id: int, db: Session, question: str = "", role: Optional[str] = None
    ) -> tuple[bool, str]:
        """异步检查用户是否有权使用 SQL 工具"""
        return await self.can_use_tool_async(user_id, db, "sql", role=role)

    async def can_access_mongodb_logs_async(
        self, user_id: int, db: Session, question: str = "", role: Optional[str] = None
    ) -> tuple[bool, str]:
        """异步检查用户是否有权查询 MongoDB 日志"""
        return await self.can_use_tool_async(user_id, db, "mongodb", role=role)

    async def can_use_tool_async(
        self,
        user_id: int,
        db: Session,
        tool_type: str,
        role: Optional[str] = None,
    ) -> tuple[bool, str]:
        """异步检查用户是否有权使用指定工具

        权限语义：登录用户一律可用，admin 全量数据，非 admin 由工具层强制
        user_id = 当前用户 的行级范围（作用域写入本请求的 contextvars）
        """
        if not user_id:
            clear_tool_scope()
            tool_name: str = "数据库查询" if tool_type == "sql" else "日志查询"
            return (
                False,
                Messages.TOOL_ACCESS_LOGIN_REQUIRED(tool_name),
            )

        if role is None:
            role = await self.get_user_role_async(user_id, db)

        self.apply_tool_scope(user_id, role)

        if role == Messages.ROLE_ADMIN:
            Logger.info(Messages.ADMIN_TOOL_ACCESS_GRANTED(user_id, role, tool_type))
        else:
            Logger.info(Messages.TOOL_ACCESS_SCOPED_GRANTED(user_id, role, tool_type))
        return True, ""

    async def validate_database_query_permission_async(
        self, user_id: int, db: Session, question: str = "", role: Optional[str] = None
    ) -> tuple[bool, str]:
        """异步验证用户是否有权执行数据库查询"""
        return await self.can_use_tool_async(user_id, db, "sql", role=role)


@lru_cache
def get_user_permission_manager(
    user_mapper: Optional[Any] = None,
) -> UserPermissionManager:
    """获取用户权限管理器单例"""
    return UserPermissionManager(user_mapper, get_spring_client())
