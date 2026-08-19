from functools import wraps
from typing import Any, Callable, Optional

from app.common.middleware import get_current_user_id
from app.core.base import Logger
from app.core.constants import HttpCode, Messages
from app.core.errors import BusinessException
from app.internal.clients import SpringClient


def requireAdmin(func: Callable[..., Any]) -> Callable[..., Any]:
    """管理员权限检查装饰器"""

    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        user_id: Optional[int] = get_current_user_id()
        if not user_id:
            Logger.warning(Messages.USER_NOT_LOGGED_IN_MESSAGE)
            raise BusinessException(
                Messages.USER_NOT_LOGGED_IN_MESSAGE,
                HttpCode.UNAUTHORIZED,
                Messages.ERROR_USER_NOT_LOGIN,
            )

        try:
            users = await SpringClient().get_users_by_ids([int(user_id)])
            user_role: str = (
                users[0].get("role") or Messages.ROLE_USER
                if users
                else Messages.ROLE_USER
            )
            if user_role != Messages.ROLE_ADMIN:
                Logger.warning(Messages.ADMIN_PERMISSION_DENIED(user_id, user_role))
                raise BusinessException(
                    Messages.USER_NO_ADMIN_PERMISSION_MESSAGE,
                    HttpCode.FORBIDDEN,
                    Messages.ERROR_USER_NO_ADMIN_PERMISSION,
                )
            Logger.info(Messages.ADMIN_ACCESS_GRANTED(user_id))
            return await func(*args, **kwargs)
        except BusinessException:
            raise
        except Exception as error:
            Logger.error(Messages.ADMIN_PERMISSION_CHECK_FAILED(error))
            raise BusinessException(
                Messages.PERMISSION_CHECK_FAILED_MESSAGE,
                HttpCode.FORBIDDEN,
                Messages.ERROR_PERMISSION_CHECK_FAILED,
            )

    return async_wrapper
