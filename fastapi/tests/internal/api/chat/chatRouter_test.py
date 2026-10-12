"""ChatRouter 对外接口契约测试

普通聊天与流式聊天都服务外部调用（前端经网关访问），不得要求内部服务令牌；
曾被误判为「零调用的内部接口」，这里固化契约防止回归
"""

from typing import Any

from fastapi.routing import APIRoute

from app.core.decorators import requireInternalToken
from app.internal.api.chat.chatRouter import router


def _endpoint(path: str) -> Any:
    """按路径取出路由端点函数"""
    for route in router.routes:
        if isinstance(route, APIRoute) and route.path == path:
            return route.endpoint
    raise AssertionError(f"路由未注册: {path}")


# 聊天接口都是对外接口，不得挂内部服务令牌校验
def test_chat_endpoints_do_not_require_internal_token() -> None:
    for path in ("/chat/models", "/chat/send", "/chat/stream"):
        endpoint = _endpoint(path)
        assert not getattr(endpoint, "requires_internal_token", False), path


# 内部令牌装饰器必须留下标记，否则上面的契约断言会因标记缺失而失效
def test_require_internal_token_marks_endpoint() -> None:
    @requireInternalToken
    async def protected() -> None:
        return None

    assert getattr(protected, "requires_internal_token", False) is True
