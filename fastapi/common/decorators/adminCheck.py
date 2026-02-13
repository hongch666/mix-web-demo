import inspect
from functools import wraps
from typing import Callable, Any, Optional
from sqlmodel import Session
from common.middleware import get_current_user_id
from common.exceptions import BusinessException
from common.config import get_db
from api.mapper import get_user_mapper
from common.utils import fileLogger as logger, Constants

def requireAdmin(func: Callable) -> Callable:
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
            logger.warning(Constants.USER_NOT_LOGGED_IN_MESSAGE)
            raise BusinessException(Constants.USER_NOT_LOGGED_IN_MESSAGE)
        
        # 获取数据库会话
        db: Optional[Session] = kwargs.get('db')
        if not db:
            # 如果kwargs中没有db，尝试从args中获取或者创建新的
            for arg in args:
                if isinstance(arg, Session):
                    db = arg
                    break
        
        if not db:
            db = next(get_db())
        
        try:
            # 获取用户Mapper
            user_mapper = get_user_mapper()
            
            # 获取用户角色
            user_role: str = user_mapper.get_user_role(int(user_id), db)
            
            # 检查是否是管理员
            if user_role != Constants.ROLE_ADMIN:
                logger.warning(f"权限不足: 用户 {user_id} 尝试访问管理员接口，角色: {user_role}")
                raise BusinessException(Constants.USER_NO_ADMIN_PERMISSION_MESSAGE)
            
            logger.info(f"管理员 {user_id} 访问受保护的接口")
            
            # 如果检查通过，执行原函数
            return await func(*args, **kwargs)
        
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"检查管理员权限时出错: {e}")
            raise BusinessException(Constants.PERMISSION_CHECK_FAILED_MESSAGE)
    
    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        # 获取当前用户ID
        user_id: Optional[str] = get_current_user_id()
        
        # 检查用户是否登录
        if not user_id:
            logger.warning(Constants.USER_NOT_LOGGED_IN_MESSAGE)
            raise BusinessException(Constants.USER_NOT_LOGGED_IN_MESSAGE)
        
        # 获取数据库会话
        db: Optional[Session] = kwargs.get('db')
        if not db:
            # 如果kwargs中没有db，尝试从args中获取或者创建新的
            for arg in args:
                if isinstance(arg, Session):
                    db = arg
                    break
        
        if not db:
            db = next(get_db())
        
        try:
            # 获取用户Mapper
            user_mapper = get_user_mapper()
            
            # 获取用户角色
            user_role: str = user_mapper.get_user_role(int(user_id), db)
            
            # 检查是否是管理员
            if user_role != Constants.ROLE_ADMIN:
                logger.warning(f"权限不足: 用户 {user_id} 尝试访问管理员接口，角色: {user_role}")
                raise BusinessException(Constants.USER_NO_ADMIN_PERMISSION_MESSAGE)
            
            logger.info(f"管理员 {user_id} 访问受保护的接口")
            
            # 如果检查通过，执行原函数
            return func(*args, **kwargs)
        
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"检查管理员权限时出错: {e}")
            raise BusinessException(Constants.PERMISSION_CHECK_FAILED_MESSAGE)
    
    # 判断是否是异步函数
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
