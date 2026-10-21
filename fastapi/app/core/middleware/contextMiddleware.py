import contextvars
from collections.abc import Awaitable, Callable
from typing import Optional

from fastapi import Request, Response
from opentelemetry.trace import get_current_span

from app.core.constants import TelemetryConstants
from starlette.middleware.base import BaseHTTPMiddleware

user_id_ctx_var: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar(
    "user_id", default=None
)
username_ctx_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "username", default=None
)
session_id_ctx_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "session_id", default=None
)
token_ctx_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "token", default=None
)
internal_token_ctx_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "internal_token", default=None
)


def get_current_user_id() -> Optional[int]:
    """从上下文变量获取当前请求的登录用户 ID"""
    return user_id_ctx_var.get()


def get_current_username() -> Optional[str]:
    """从上下文变量获取当前请求的用户名"""
    return username_ctx_var.get()


def get_current_session_id() -> Optional[str]:
    """从上下文变量获取当前请求的会话 ID"""
    return session_id_ctx_var.get()


def get_current_token() -> Optional[str]:
    """从上下文变量获取当前请求的用户访问令牌"""
    return token_ctx_var.get()


def get_current_internal_token() -> Optional[str]:
    """从上下文变量获取当前请求的内部服务令牌"""
    return internal_token_ctx_var.get()


def get_current_trace_id() -> Optional[str]:
    """获取当前 OpenTelemetry 链路 span 的 trace_id 并格式化为固定宽度十六进制，无有效链路时返回 None"""
    span_context = get_current_span().get_span_context()
    if span_context.is_valid:
        return format(
            span_context.trace_id,
            f"0{TelemetryConstants.TRACE_ID_HEX_WIDTH}x",
        )
    return None


def _extract_bearer_token(header: Optional[str]) -> Optional[str]:
    """从 Authorization 头中提取 Bearer token"""
    if header and header.startswith("Bearer "):
        return header[7:]
    return None


class ContextMiddleware(BaseHTTPMiddleware):
    """请求上下文中间件，从请求头提取用户身份、会话与令牌写入 contextvars 供全链路读取"""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """解析请求头中的用户 ID、用户名、会话 ID 与两类令牌并设置到上下文，请求结束后重置全部上下文变量"""
        raw_user_id: Optional[str] = request.headers.get("X-User-Id")
        user_id: Optional[int] = None
        if raw_user_id:
            try:
                user_id = int(raw_user_id)
            except ValueError:
                user_id = None
        username: Optional[str] = request.headers.get("X-Username")
        session_id: Optional[str] = request.headers.get("X-Session-Id")
        token: Optional[str] = _extract_bearer_token(
            request.headers.get("Authorization")
        )
        internal_token: Optional[str] = _extract_bearer_token(
            request.headers.get("X-Internal-Token")
        )
        user_id_token: contextvars.Token[Optional[int]] = user_id_ctx_var.set(user_id)
        username_token: contextvars.Token[Optional[str]] = username_ctx_var.set(
            username
        )
        session_id_token: contextvars.Token[Optional[str]] = session_id_ctx_var.set(
            session_id
        )
        token_token: contextvars.Token[Optional[str]] = token_ctx_var.set(token)
        internal_token_token: contextvars.Token[Optional[str]] = (
            internal_token_ctx_var.set(internal_token)
        )
        try:
            response: Response = await call_next(request)
        finally:
            user_id_ctx_var.reset(user_id_token)
            username_ctx_var.reset(username_token)
            session_id_ctx_var.reset(session_id_token)
            token_ctx_var.reset(token_token)
            internal_token_ctx_var.reset(internal_token_token)
        return response
