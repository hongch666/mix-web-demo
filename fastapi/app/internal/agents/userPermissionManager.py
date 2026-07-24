from functools import lru_cache
from typing import Any, Optional, Tuple

from app.core.base import Logger
from app.core.constants import Defaults, Messages
from sqlalchemy.orm import Session


class UserPermissionManager:
    """用户权限管理器"""

    def __init__(self, user_mapper: Optional[Any] = None) -> None:
        """
        初始化权限管理器

        Args:
            user_mapper: 用户 Mapper 实例
        """
        self.user_mapper: Optional[Any] = user_mapper

    async def get_user_role_async(self, user_id: int, db: Session) -> Optional[str]:
        """异步获取用户角色"""
        try:
            if not self.user_mapper:
                Logger.warning(Messages.USER_ROLE_MAPPER_UNINITIALIZED(user_id))
                return Messages.ROLE_USER

            role: Optional[str] = await self.user_mapper.get_user_role_async(
                user_id, db
            )
            role = role or Messages.ROLE_USER
            Logger.info(Messages.USER_ROLE_LOADED(user_id, role))
            return role
        except Exception as e:
            Logger.error(Messages.USER_ROLE_LOAD_FAILED(user_id, e))
            return Messages.ROLE_USER

    async def is_admin_async(self, user_id: int, db: Session) -> bool:
        role: Optional[str] = await self.get_user_role_async(user_id, db)
        return role == Messages.ROLE_ADMIN

    async def is_personal_info_query(self, question: str) -> bool:
        """
        判断问题是否涉及个人信息查询

        Args:
            question: 用户问题

        Returns:
            True 如果是个人信息查询，否则 False
        """
        if not question:
            return False

        # 转换为小写便于匹配
        question_lower: str = question.lower()

        # 检查是否包含个人信息查询的关键字
        for keyword in Defaults.PERSONAL_INFO_KEYWORDS:
            if keyword in question_lower:
                Logger.debug(Messages.PERSONAL_INFO_KEYWORD_DETECTED(keyword))
                return True

        return False

    async def can_access_sql_tools_async(
        self, user_id: int, db: Session, question: str = ""
    ) -> Tuple[bool, str]:
        """异步检查用户是否有权使用 SQL 工具"""
        return await self.can_use_tool_async(user_id, db, "sql", question)

    async def can_access_mongodb_logs_async(
        self, user_id: int, db: Session, question: str = ""
    ) -> Tuple[bool, str]:
        """异步检查用户是否有权查询 MongoDB 日志"""
        return await self.can_use_tool_async(user_id, db, "mongodb", question)

    async def can_use_tool_async(
        self, user_id: int, db: Session, tool_type: str, question: str = ""
    ) -> Tuple[bool, str]:
        """异步检查用户是否有权使用指定工具"""
        if not user_id:
            tool_name: str = "数据库查询" if tool_type == "sql" else "日志查询"
            return (
                False,
                Messages.TOOL_ACCESS_LOGIN_REQUIRED(tool_name),
            )

        if question and await self.is_personal_info_query(question):
            Logger.info(Messages.PERSONAL_TOOL_ACCESS_GRANTED(user_id, tool_type))
            return True, ""

        role: Optional[str] = await self.get_user_role_async(user_id, db)
        if role == Messages.ROLE_ADMIN:
            Logger.info(Messages.ADMIN_TOOL_ACCESS_GRANTED(user_id, role, tool_type))
            return True, ""

        tool_name: str = "数据库查询" if tool_type == "sql" else "日志查询"
        reason: str = Messages.TOOL_ACCESS_DENIED_REASON(tool_name)
        Logger.warning(Messages.TOOL_ACCESS_DENIED_LOG(user_id, role, tool_type, question))
        return False, reason

    async def validate_database_query_permission_async(
        self, user_id: int, db: Session, question: str = ""
    ) -> Tuple[bool, str]:
        """异步验证用户是否有权执行数据库查询"""
        return await self.can_use_tool_async(user_id, db, "sql", question)


@lru_cache
def get_user_permission_manager(
    user_mapper: Optional[Any] = None,
) -> UserPermissionManager:
    """获取用户权限管理器单例"""
    return UserPermissionManager(user_mapper)
