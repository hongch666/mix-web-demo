import asyncio
from functools import wraps
from typing import Any, Callable, Optional

from app.common.middleware import get_current_user_id
from app.core.base import Constants, Logger
from app.core.db import get_db
from app.core.errors import BusinessException
from app.internal.crud import get_user_mapper
from sqlalchemy.orm import Session


def requireAdmin(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    管理员权限检查装饰器

    检查当前用户是否是管理员，如果不是则拦截请求并抛出异常。

    使用方式:
        @router.get("/admin-only")
        @requireAdmin
        async def admin_only_endpoint(db: Session = Depends(get_db)):
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
            Logger.warning(Constants.USER_NOT_LOGGED_IN_MESSAGE)
            raise BusinessException(Constants.USER_NOT_LOGGED_IN_MESSAGE)

        # 获取数据库会话
        db: Optional[Session] = kwargs.get("db")
        if not db:
            for arg in args:
                if isinstance(arg, Session):
                    db = arg
                    break

        def _check_permission(current_db: Session) -> None:
            # 获取用户Mapper
            user_mapper = get_user_mapper()

            # 获取用户角色
            user_role: str = user_mapper.get_user_role(int(user_id), current_db)

            # 检查是否是管理员
            if user_role != Constants.ROLE_ADMIN:
                Logger.warning(
                    f"权限不足: 用户 {user_id} 尝试访问管理员接口，角色: {user_role}"
                )
                raise BusinessException(Constants.USER_NO_ADMIN_PERMISSION_MESSAGE)

            Logger.info(f"管理员 {user_id} 访问受保护的接口")

        try:
            if db:
                await asyncio.to_thread(_check_permission, db)
                return await func(*args, **kwargs)
            db_generator = get_db()
            current_db = await anext(db_generator)
            try:
                await asyncio.to_thread(_check_permission, current_db)
                return await func(*args, **kwargs)
            finally:
                await db_generator.aclose()

        except BusinessException:
            raise
        except Exception as e:
            Logger.error(f"检查管理员权限时出错: {e}")
            raise BusinessException(Constants.PERMISSION_CHECK_FAILED_MESSAGE)

    return async_wrapper
