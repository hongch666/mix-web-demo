from collections.abc import Callable
from functools import wraps
from typing import Any, Optional

from app.core.auth import AdminChecker, build_admin_checker
from app.core.base import Logger
from app.core.constants import HttpCode, Messages
from app.core.errors import BusinessException
from app.core.middleware import get_current_user_id
from app.internal.clients import get_spring_client


def requireAdmin(
    func: Optional[Callable[..., Any]] = None,
    *,
    admin_checker: Optional[AdminChecker] = None,
) -> Callable[..., Any]:
    """管理员权限检查装饰器"""

    def decorator(target: Callable[..., Any]) -> Callable[..., Any]:
        """包装目标异步函数，在执行前插入管理员权限校验逻辑"""

        @wraps(target)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            """选择校验器（注入或默认）并执行管理员权限检查，通过后调用原函数"""
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
    """校验当前登录用户是否为管理员，未登录或非管理员抛出对应业务异常，校验异常统一转换为权限检查失败"""
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
    """使用默认 Spring 客户端构造管理员校验器并查询用户角色"""
    return await build_admin_checker(get_spring_client())(user_id)
