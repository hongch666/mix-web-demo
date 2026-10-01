from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, Optional

from app.common.middleware import get_current_user_id
from app.core.base import Logger
from app.core.constants import HttpCode, Messages
from app.core.errors import BusinessException
from app.internal.clients import SpringClient, get_spring_client

AdminChecker = Callable[[int], Awaitable[bool]]


def build_admin_checker(spring_client: SpringClient) -> AdminChecker:
    """基于已注入的 Spring 客户端创建管理员检查器"""

    async def checker(user_id: int) -> bool:
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


def requireAdmin(
    func: Optional[Callable[..., Any]] = None,
    *,
    admin_checker: Optional[AdminChecker] = None,
) -> Callable[..., Any]:
    """管理员权限检查装饰器"""

    def decorator(target: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(target)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            checker: AdminChecker = admin_checker or _default_admin_checker
            return await _run_admin_check(checker, target, args, kwargs)

        return async_wrapper

    if func is not None:
        return decorator(func)
    return decorator


async def _run_admin_check(
    checker: AdminChecker,
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    user_id: Optional[int] = get_current_user_id()
    if not user_id:
        Logger.warning(Messages.USER_NOT_LOGGED_IN_MESSAGE)
        raise BusinessException(
            Messages.USER_NOT_LOGGED_IN_MESSAGE,
            HttpCode.UNAUTHORIZED,
            Messages.ERROR_USER_NOT_LOGIN,
        )

    try:
        if not await checker(int(user_id)):
            Logger.warning(
                Messages.ADMIN_PERMISSION_DENIED(user_id, Messages.ROLE_USER)
            )
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
        ) from error


async def _default_admin_checker(user_id: int) -> bool:
    return await build_admin_checker(get_spring_client())(user_id)
