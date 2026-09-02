from collections.abc import Awaitable, Callable
from typing import Any

import grpc
from app.common.middleware.contextMiddleware import (
    internal_token_ctx_var,
    session_id_ctx_var,
    token_ctx_var,
    user_id_ctx_var,
    username_ctx_var,
)
from app.core.auth import InternalTokenUtil
from app.core.base import Logger
from app.core.constants import Messages


def _metadata_value(metadata: tuple[tuple[str, str], ...], name: str) -> str | None:
    for key, value in metadata:
        if key.lower() == name:
            return value
    return None


def _bearer_token(value: str | None) -> str | None:
    if value and value.startswith("Bearer "):
        return value[7:]
    return None


class UserContextInterceptor(grpc.aio.ServerInterceptor):
    """把 gRPC metadata 写入现有 contextvars，并在调用结束后恢复。"""

    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], Awaitable[Any]],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> Any:
        handler = await continuation(handler_call_details)
        if handler is None or handler.unary_unary is None:
            return handler

        metadata = tuple(handler_call_details.invocation_metadata or ())
        user_id_value = _metadata_value(metadata, "x-user-id")
        user_id: int | None = None
        if user_id_value:
            try:
                user_id = int(user_id_value)
            except ValueError:
                user_id = None

        async def unary_unary(request: Any, context: grpc.aio.ServicerContext) -> Any:
            tokens = (
                user_id_ctx_var.set(user_id),
                username_ctx_var.set(_metadata_value(metadata, "x-username")),
                session_id_ctx_var.set(_metadata_value(metadata, "x-session-id")),
                token_ctx_var.set(
                    _bearer_token(_metadata_value(metadata, "authorization"))
                ),
                internal_token_ctx_var.set(
                    _bearer_token(_metadata_value(metadata, "x-internal-token"))
                ),
            )
            try:
                Logger.debug(Messages.GRPC_CONTEXT_RECEIVED(user_id))
                return await handler.unary_unary(request, context)
            finally:
                user_id_ctx_var.reset(tokens[0])
                username_ctx_var.reset(tokens[1])
                session_id_ctx_var.reset(tokens[2])
                token_ctx_var.reset(tokens[3])
                internal_token_ctx_var.reset(tokens[4])

        return grpc.unary_unary_rpc_method_handler(
            unary_unary,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )


class InternalTokenInterceptor(grpc.aio.ServerInterceptor):
    """验证内部服务令牌，保持与 HTTP 内部接口相同的安全边界。"""

    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], Awaitable[Any]],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> Any:
        handler = await continuation(handler_call_details)
        if handler is None or handler.unary_unary is None:
            return handler

        async def unary_unary(request: Any, context: grpc.aio.ServicerContext) -> Any:
            token = _bearer_token(
                _metadata_value(
                    tuple(handler_call_details.invocation_metadata or ()),
                    "x-internal-token",
                )
            )
            if not token:
                await context.abort(
                    grpc.StatusCode.UNAUTHENTICATED,
                    Messages.GRPC_INTERNAL_TOKEN_MISSING,
                )
            try:
                InternalTokenUtil().validate_internal_token(token)
            except Exception as error:
                Logger.warning(Messages.GRPC_INTERNAL_TOKEN_INVALID(error))
                await context.abort(
                    grpc.StatusCode.UNAUTHENTICATED,
                    Messages.GRPC_INTERNAL_TOKEN_INVALID_MESSAGE,
                )
            return await handler.unary_unary(request, context)

        return grpc.unary_unary_rpc_method_handler(
            unary_unary,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )
