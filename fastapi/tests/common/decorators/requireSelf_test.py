import asyncio
import importlib
from unittest.mock import AsyncMock, Mock

import pytest

from app.common.decorators import requireSelf
from app.core.errors import BusinessException

require_self_module = importlib.import_module("app.common.decorators.requireSelf")


# 访问自身资源放行且不查询管理员权限
def test_allows_current_user_without_admin_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin_check = AsyncMock(return_value=False)
    monkeypatch.setattr(require_self_module, "get_current_user_id", lambda: 7)
    monkeypatch.setattr(require_self_module, "_is_admin", admin_check)

    @requireSelf
    async def endpoint(*, user_id: int) -> int:
        return user_id

    assert asyncio.run(endpoint(user_id=7)) == 7
    admin_check.assert_not_awaited()


# 管理员访问他人资源放行并以其身份查询管理员权限
def test_allows_admin_to_access_another_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin_check = AsyncMock(return_value=True)
    monkeypatch.setattr(require_self_module, "get_current_user_id", lambda: 7)
    monkeypatch.setattr(require_self_module, "_is_admin", admin_check)

    @requireSelf
    async def endpoint(*, user_id: int) -> int:
        return user_id

    assert asyncio.run(endpoint(user_id=8)) == 8
    admin_check.assert_awaited_once_with(7)


# 未登录、缺少目标用户、越权访问分别返回 401/400/403
@pytest.mark.parametrize(
    ("current_user_id", "target_user_id", "expected_status"),
    [(None, 8, 401), (7, None, 400), (7, 8, 403)],
)
def test_rejects_invalid_user_scope(
    monkeypatch: pytest.MonkeyPatch,
    current_user_id: int | None,
    target_user_id: int | None,
    expected_status: int,
) -> None:
    monkeypatch.setattr(
        require_self_module, "get_current_user_id", lambda: current_user_id
    )
    monkeypatch.setattr(require_self_module, "_is_admin", AsyncMock(return_value=False))

    @requireSelf
    async def endpoint(*, user_id: int | None = None) -> int | None:
        return user_id

    with pytest.raises(BusinessException) as error:
        asyncio.run(endpoint(user_id=target_user_id))

    assert error.value.status_code == expected_status


# 管理员校验异常时 fail-closed 返回 403
def test_admin_lookup_failure_is_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spring_client = Mock()
    spring_client.get_users_by_ids = AsyncMock(side_effect=RuntimeError("unavailable"))
    monkeypatch.setattr(require_self_module, "get_current_user_id", lambda: 7)
    monkeypatch.setattr("app.internal.clients.get_spring_client", lambda: spring_client)

    @requireSelf
    async def endpoint(*, user_id: int) -> int:
        return user_id

    with pytest.raises(BusinessException) as error:
        asyncio.run(endpoint(user_id=8))

    assert error.value.status_code == 403


# 同步接口被装饰时抛 TypeError
def test_rejects_synchronous_endpoint() -> None:
    def endpoint(*, user_id: int) -> int:
        return user_id

    with pytest.raises(TypeError):
        requireSelf(endpoint)
