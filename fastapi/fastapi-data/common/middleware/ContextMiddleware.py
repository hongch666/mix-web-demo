import contextvars
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Callable, Awaitable

user_id_ctx_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("user_id", default=None)
username_ctx_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("username", default=None)

def get_current_user_id() -> Optional[str]:
    return user_id_ctx_var.get()

def get_current_username() -> Optional[str]:
    return username_ctx_var.get()

class ContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, 
        request: Request, 
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        user_id: Optional[str] = request.headers.get("X-User-Id")
        username: Optional[str] = request.headers.get("X-Username")
        user_id_token: contextvars.Token = user_id_ctx_var.set(user_id)
        username_token: contextvars.Token = username_ctx_var.set(username)
        try:
            response: Response = await call_next(request)
        finally:
            user_id_ctx_var.reset(user_id_token)
            username_ctx_var.reset(username_token)
        return response