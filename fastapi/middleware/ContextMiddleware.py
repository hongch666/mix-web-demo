import contextvars
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

user_id_ctx_var = contextvars.ContextVar("user_id", default=None)
username_ctx_var = contextvars.ContextVar("username", default=None)

def get_current_user_id():
    return user_id_ctx_var.get()

def get_current_username():
    return username_ctx_var.get()

class ContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        user_id = request.headers.get("X-User-Id")
        username = request.headers.get("X-Username")
        user_id_token = user_id_ctx_var.set(user_id)
        username_token = username_ctx_var.set(username)
        try:
            response = await call_next(request)
        finally:
            user_id_ctx_var.reset(user_id_token)
            username_ctx_var.reset(username_token)
        return response