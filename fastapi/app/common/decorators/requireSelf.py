from collections.abc import Callable
from functools import wraps
from inspect import iscoroutinefunction
from typing import Any, Optional

from app.common.middleware import get_current_user_id
from app.core.base import Logger
from app.core.constants import HttpCode, Messages
from app.core.errors import BusinessException


def requireSelf[T: Callable[..., Any]](func: Optional[T] = None) -> Callable[..., Any]:
    """
    校验请求中的 user_id 与上下文登录用户一致的装饰器
    管理员可访问任意用户，其余用户仅能访问自身数据

    依赖装饰器把被校验的值写入 kwargs["user_id"]，因此与业务参数名绑定：
    被装饰函数必须使用 user_id 作为查询参数名（外部仍可传 user_id 查询串）

    :example
    @requireSelf
    async def endpoint(..., user_id: int = Query(alias="user_id")) -> ...:
        ...
    """

    def decorator(f: T) -> T:
        if not iscoroutinefunction(f):
            raise TypeError(Messages.REQUIRE_SELF_ASYNC_ERROR)

        @wraps(f)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            current_user_id: Optional[int] = get_current_user_id()
            if current_user_id is None:
                Logger.warning(Messages.USER_IDENTITY_MISSING_MESSAGE)
                raise BusinessException(
                    Messages.USER_NOT_LOGGED_IN_MESSAGE,
                    HttpCode.UNAUTHORIZED,
                    Messages.ERROR_USER_NOT_LOGIN,
                )

            target_user_id: Optional[int] = kwargs.get("user_id")
            if target_user_id is None:
                Logger.warning(Messages.USER_SCOPE_TARGET_MISSING_MESSAGE)
                raise BusinessException(
                    Messages.USER_SCOPE_TARGET_MISSING_MESSAGE,
                    HttpCode.BAD_REQUEST,
                    Messages.ERROR_USER_SCOPE_TARGET_MISSING,
                )

            # 访问自身数据无需远程查询角色，避免给常规路径引入额外调用
            if int(target_user_id) != int(current_user_id):
                if not await _is_admin(current_user_id):
                    Logger.warning(
                        Messages.USER_SCOPE_DENIED(current_user_id, int(target_user_id))
                    )
                    raise BusinessException(
                        Messages.USER_SCOPE_FORBIDDEN_MESSAGE,
                        HttpCode.FORBIDDEN,
                        Messages.ERROR_USER_SCOPE_FORBIDDEN,
                    )
                Logger.info(
                    Messages.USER_SCOPE_ADMIN_ACCESS(
                        current_user_id, int(target_user_id)
                    )
                )

            return await f(*args, **kwargs)

        return async_wrapper

    if callable(func):
        return decorator(func)
    return decorator


async def _is_admin(user_id: int) -> bool:
    """经 Spring 查询用户角色，查询失败按非管理员处理"""
    from app.internal.clients import get_spring_client

    try:
        users: list[dict[str, Any]] = await get_spring_client().get_users_by_ids(
            [int(user_id)]
        )
        role: str = (
            users[0].get("role") or Messages.ROLE_USER if users else Messages.ROLE_USER
        )
        return role == Messages.ROLE_ADMIN
    except Exception as error:
        Logger.error(Messages.ADMIN_PERMISSION_CHECK_FAILED(error))
        return False
