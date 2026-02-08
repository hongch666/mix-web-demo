from functools import wraps
from typing import Callable, TypeVar, Optional, Any, Dict
from fastapi import Request
from common.exceptions import BusinessException
from common.utils import Constants, fileLogger as logger, InternalTokenUtil

T = TypeVar('T', bound=Callable[..., Any])


def requireInternalToken(func: Optional[T] = None, *, required_service_name: Optional[str] = None) -> Callable:
    """
    需要内部服务令牌验证的装饰器
    用于标记需要内部服务令牌才能访问的接口

    :param func: 被装饰的函数（未指派service名时自动注入）
    :param required_service_name: 可选参数，指定必须来自特定服务的令牌
    :example
    @requireInternalToken
    async def get_fastapi() -> Dict[str, str]:
        return {"data": "success"}

    @requireInternalToken()
    async def get_fastapi2() -> Dict[str, str]:
        return {"data": "success"}

    @requireInternalToken(required_service_name="spring")
    async def get_protected() -> Dict[str, str]:
        return {"data": "success"}
    """
    
    # 绑定service名到闭包中，供后续的装饰器使用
    service_name = required_service_name

    def decorator(f: T) -> T:
        @wraps(f)
        async def async_wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
            # 获取请求头中的内部令牌
            auth_header: str = request.headers.get("X-Internal-Token", "")

            if not auth_header:
                logger.error(Constants.INTERNAL_TOKEN_MISSING)
                raise BusinessException(Constants.INTERNAL_TOKEN_MISSING)

            # 移除 "Bearer " 前缀
            token: str = auth_header
            if token.startswith("Bearer "):
                token = token[7:]

            try:
                # 验证令牌
                internal_token_util: InternalTokenUtil = InternalTokenUtil()
                claims: Dict[str, Any] = internal_token_util.validate_internal_token(token)

                # 验证服务名称（如果指定了）
                if service_name and claims.get("serviceName") != service_name:
                    error_msg: str = f"{Constants.SERVICE_NAME_MISMATCH}. 期望: {service_name}, 获得: {claims.get('serviceName')}"
                    logger.error(error_msg)
                    raise BusinessException(Constants.SERVICE_NAME_MISMATCH)

                logger.debug(
                    f"内部令牌验证成功 - 用户ID: {claims.get('userId')}, 服务: {claims.get('serviceName')}"
                )

                # 将令牌信息存储到请求中供后续使用
                request.state.internal_token_claims = claims

                # 调用原始函数
                return await f(request, *args, **kwargs)
            except BusinessException:
                raise
            except Exception as e:
                logger.error(f"令牌验证失败: {str(e)}")
                raise BusinessException(Constants.INTERNAL_TOKEN_INVALID)

        @wraps(f)
        def sync_wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
            # 获取请求头中的内部令牌
            auth_header: str = request.headers.get("X-Internal-Token", "")

            if not auth_header:
                logger.error(Constants.INTERNAL_TOKEN_MISSING)
                raise BusinessException(Constants.INTERNAL_TOKEN_MISSING)

            # 移除 "Bearer " 前缀
            token: str = auth_header
            if token.startswith("Bearer "):
                token = token[7:]

            try:
                # 验证令牌
                internal_token_util: InternalTokenUtil = InternalTokenUtil()
                claims: Dict[str, Any] = internal_token_util.validate_internal_token(token)

                # 验证服务名称（如果指定了）
                if service_name and claims.get("serviceName") != service_name:
                    error_msg: str = f"{Constants.SERVICE_NAME_MISMATCH}. 期望: {service_name}, 获得: {claims.get('serviceName')}"
                    logger.error(error_msg)
                    raise BusinessException(Constants.SERVICE_NAME_MISMATCH)

                logger.debug(
                    f"内部令牌验证成功 - 用户ID: {claims.get('userId')}, 服务: {claims.get('serviceName')}"
                )

                # 将令牌信息存储到请求中供后续使用
                request.state.internal_token_claims = claims

                # 调用原始函数
                return f(request, *args, **kwargs)
            except BusinessException:
                raise
            except Exception as e:
                logger.error(f"令牌验证失败: {str(e)}")
                raise BusinessException(Constants.INTERNAL_TOKEN_INVALID)

        # 判断是否为异步函数
        if hasattr(f, "__wrapped__") or (
            hasattr(f, "__code__") and f.__code__.co_flags & 0x80
        ):
            return async_wrapper
        else:
            return sync_wrapper

    # 如果 func 是可调用的且不是字符串，说明被直接用作装饰器（@requireInternalToken）
    if callable(func):
        return decorator(func)
    # 否则返回 decorator，供后续的路由函数使用（@requireInternalToken() 或 @requireInternalToken(required_service_name="xxx")）
    else:
        return decorator
