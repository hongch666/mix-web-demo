import contextvars
from collections.abc import Awaitable, Callable
from typing import Optional

from fastapi import Request, Response
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
    return user_id_ctx_var.get()


def get_current_username() -> Optional[str]:
    return username_ctx_var.get()


def get_current_session_id() -> Optional[str]:
    return session_id_ctx_var.get()


def get_current_token() -> Optional[str]:
    return token_ctx_var.get()


def get_current_internal_token() -> Optional[str]:
    return internal_token_ctx_var.get()


def _extract_bearer_token(header: Optional[str]) -> Optional[str]:
    """从 Authorization 头中提取 Bearer token"""
    if header and header.startswith("Bearer "):
        return header[7:]
    return None


class ContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
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
        user_id_token: contextvars.Token = user_id_ctx_var.set(user_id)
        username_token: contextvars.Token = username_ctx_var.set(username)
        session_id_token: contextvars.Token = session_id_ctx_var.set(session_id)
        token_token: contextvars.Token = token_ctx_var.set(token)
        internal_token_token: contextvars.Token = internal_token_ctx_var.set(
            internal_token
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
