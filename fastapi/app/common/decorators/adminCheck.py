from collections.abc import AsyncGenerator
from functools import wraps
from typing import Any, Callable, Optional

from app.common.middleware import get_current_user_id
from app.core.base import Logger
from app.core.constants import HttpCode, Messages
from app.core.db import get_db
from app.core.errors import BusinessException
from app.internal.crud import UserMapper, get_user_mapper
from sqlalchemy.ext.asyncio import AsyncSession


def requireAdmin(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    管理员权限检查装饰器

    检查当前用户是否是管理员，如果不是则拦截请求并抛出异常

    使用方式:
        @router.get("/admin-only")
        @requireAdmin
        async def admin_only_endpoint(db: AsyncSession = Depends(get_db)):
            # 只有管理员才能执行这个函数
            pass

    Raises:
        BusinessException: 如果用户不是管理员或用户未登录
    """

    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        # 获取当前用户ID
        user_id: Optional[str] = get_current_user_id()

        # 检查用户是否登录
        if not user_id:
            Logger.warning(Messages.USER_NOT_LOGGED_IN_MESSAGE)
            raise BusinessException(
                Messages.USER_NOT_LOGGED_IN_MESSAGE,
                HttpCode.UNAUTHORIZED,
                Messages.ERROR_USER_NOT_LOGIN,
            )

        # 获取数据库会话
        db: Optional[AsyncSession] = kwargs.get("db")
        if not db:
            for arg in args:
                if isinstance(arg, AsyncSession):
                    db = arg
                    break

        try:
            if db:
                user_mapper: UserMapper = get_user_mapper()
                user_role: str = await user_mapper.get_user_role_async(int(user_id), db)
                if user_role != Messages.ROLE_ADMIN:
                    Logger.warning(Messages.ADMIN_PERMISSION_DENIED(user_id, user_role))
                    raise BusinessException(
                        Messages.USER_NO_ADMIN_PERMISSION_MESSAGE,
                        HttpCode.FORBIDDEN,
                        Messages.ERROR_USER_NO_ADMIN_PERMISSION,
                    )
                Logger.info(Messages.ADMIN_ACCESS_GRANTED(user_id))
                return await func(*args, **kwargs)
            db_generator: AsyncGenerator[AsyncSession, None] = get_db()
            current_db: AsyncSession = await anext(db_generator)
            try:
                user_mapper: UserMapper = get_user_mapper()
                user_role: str = await user_mapper.get_user_role_async(
                    int(user_id), current_db
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
            finally:
                await db_generator.aclose()

        except BusinessException:
            raise
        except Exception as e:
            Logger.error(Messages.ADMIN_PERMISSION_CHECK_FAILED(e))
            raise BusinessException(
                Messages.PERMISSION_CHECK_FAILED_MESSAGE,
                HttpCode.FORBIDDEN,
                Messages.ERROR_PERMISSION_CHECK_FAILED,
            )

    return async_wrapper
