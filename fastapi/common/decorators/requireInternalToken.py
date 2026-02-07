from functools import wraps
from typing import Callable, TypeVar, Optional, Any, Dict
from fastapi import Request
from common.exceptions import BusinessException
from common.utils import Constants, fileLogger as logger, InternalTokenUtil

T = TypeVar('T', bound=Callable[..., Any])


def requireInternalToken(required_service_name: Optional[str] = None) -> Callable[[T], T]:
    """
    需要内部服务令牌验证的装饰器
    用于标记需要内部服务令牌才能访问的接口

    :param required_service_name: 可选参数，指定必须来自特定服务的令牌
    :example
    @requireInternalToken()
    async def get_fastapi() -> Dict[str, str]:
        return {"data": "success"}

    @requireInternalToken(required_service_name="spring")
    async def get_protected() -> Dict[str, str]:
        return {"data": "success"}
    """

    def decorator(func: T) -> T:
        @wraps(func)
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
                if required_service_name and claims.get("serviceName") != required_service_name:
                    error_msg: str = f"{Constants.SERVICE_NAME_MISMATCH}. 期望: {required_service_name}, 获得: {claims.get('serviceName')}"
                    logger.error(error_msg)
                    raise BusinessException(Constants.SERVICE_NAME_MISMATCH)

                logger.debug(
                    f"内部令牌验证成功 - 用户ID: {claims.get('userId')}, 服务: {claims.get('serviceName')}"
                )

                # 将令牌信息存储到请求中供后续使用
                request.state.internal_token_claims = claims

                # 调用原始函数
                return await func(request, *args, **kwargs)
            except BusinessException:
                raise
            except Exception as e:
                logger.error(f"令牌验证失败: {str(e)}")
                raise BusinessException(Constants.INTERNAL_TOKEN_INVALID)

        @wraps(func)
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
                if required_service_name and claims.get("serviceName") != required_service_name:
                    error_msg: str = f"{Constants.SERVICE_NAME_MISMATCH}. 期望: {required_service_name}, 获得: {claims.get('serviceName')}"
                    logger.error(error_msg)
                    raise BusinessException(Constants.SERVICE_NAME_MISMATCH)

                logger.debug(
                    f"内部令牌验证成功 - 用户ID: {claims.get('userId')}, 服务: {claims.get('serviceName')}"
                )

                # 将令牌信息存储到请求中供后续使用
                request.state.internal_token_claims = claims

                # 调用原始函数
                return func(request, *args, **kwargs)
            except BusinessException:
                raise
            except Exception as e:
                logger.error(f"令牌验证失败: {str(e)}")
                raise BusinessException(Constants.INTERNAL_TOKEN_INVALID)

        # 判断是否为异步函数
        if hasattr(func, "__wrapped__") or (
            hasattr(func, "__code__") and func.__code__.co_flags & 0x80
        ):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
