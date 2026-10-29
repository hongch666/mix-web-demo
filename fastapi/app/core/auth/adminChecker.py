from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from app.core.base import Logger
from app.core.constants import Messages

if TYPE_CHECKING:
    from app.internal.clients import SpringClient

AdminChecker = Callable[[int], Awaitable[bool]]


def build_admin_checker(spring_client: "SpringClient") -> AdminChecker:
    """基于已注入的 Spring 客户端创建管理员检查器，查询失败时记录日志并抛出异常，降级策略由调用方决定"""

    async def checker(user_id: int) -> bool:
        """调用 Spring 接口按用户 ID 查询角色，判断该用户是否为管理员"""
        try:
            users = await spring_client.get_users_by_ids([int(user_id)])
            user_role: str = (
                users[0].get("role") or Messages.ROLE_USER
                if users
                else Messages.ROLE_USER
            )
            return user_role == Messages.ROLE_ADMIN
        except Exception as error:
            Logger.error(Messages.ADMIN_PERMISSION_CHECK_FAILED(error))
            raise

    return checker
