from functools import lru_cache
from typing import Any, List, Optional, Tuple

from app.core.base import Constants, Logger
from app.core.config import load_config
from sqlalchemy.orm import Session


class UserPermissionManager:
    """用户权限管理器"""

    # 个人信息查询的关键字 - 从配置文件加载
    @property
    def PERSONAL_INFO_KEYWORDS(self) -> List[str]:
        """动态从配置文件加载个人信息查询关键字"""
        try:
            keywords = load_config("permission", "personal_info_keywords")
            if keywords:
                return keywords
        except Exception as e:
            Logger.warning(f"从配置文件加载关键字失败: {e}，使用默认关键字")

        # 默认关键字
        return Constants.DEFAULT_KEYWORDS

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
                Logger.warning(
                    f"用户Mapper未初始化，无法获取用户 {user_id} 的角色，使用默认角色 'user'"
                )
                return Constants.ROLE_USER

            role = await self.user_mapper.get_user_role_async(user_id, db)
            role = role or Constants.ROLE_USER
            Logger.info(f"用户 {user_id} 的角色: {role}")
            return role
        except Exception as e:
            Logger.error(f"获取用户 {user_id} 的角色失败: {e}，使用默认角色 'user'")
            return Constants.ROLE_USER

    async def is_admin_async(self, user_id: int, db: Session) -> bool:
        role = await self.get_user_role_async(user_id, db)
        return role == Constants.ROLE_ADMIN

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
        question_lower = question.lower()

        # 检查是否包含个人信息查询的关键字
        for keyword in self.PERSONAL_INFO_KEYWORDS:
            if keyword in question_lower:
                Logger.debug(f"[权限] 检测到个人信息查询关键字: '{keyword}'")
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
            tool_name = "数据库查询" if tool_type == "sql" else "日志查询"
            return (
                False,
                f"权限拒绝：请先登录才能访问{tool_name}功能。您当前可以使用文章搜索和闲聊功能。",
            )

        if question and await self.is_personal_info_query(question):
            Logger.info(f"用户 {user_id} 查询个人信息，允许访问 {tool_type} 工具")
            return True, ""

        role = await self.get_user_role_async(user_id, db)
        if role == Constants.ROLE_ADMIN:
            Logger.info(f"用户 {user_id} (角色: {role}) 有权访问 {tool_type} 工具")
            return True, ""

        tool_name = "数据库查询" if tool_type == "sql" else "日志查询"
        reason = f"权限拒绝：您的账户权限不足，无法访问{tool_name}功能。仅管理员账户可以使用此功能。如需查询个人信息（如'我的点赞文章'），请在问题中包含相关关键词。"
        Logger.warning(
            f"用户 {user_id} (角色: {role}) 尝试访问 {tool_type} 工具被拒绝：{question}"
        )
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
