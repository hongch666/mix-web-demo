import asyncio
import importlib
from unittest.mock import AsyncMock, Mock

import pytest

from app.common.decorators import requireAdmin
from app.core.constants import ErrorCodes, HttpCode, Messages
from app.core.errors import BusinessException

admin_check_module = importlib.import_module("app.common.decorators.adminCheck")


def _build_spring_client(users: list[dict[str, object]]) -> tuple[Mock, AsyncMock]:
    get_users_by_ids = AsyncMock(return_value=users)
    spring_client = Mock()
    spring_client.get_users_by_ids = get_users_by_ids
    return spring_client, get_users_by_ids


def _patch_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    *,
    user_id: int | None,
    spring_client: Mock | None = None,
) -> None:
    monkeypatch.setattr(admin_check_module, "Logger", Mock())
    monkeypatch.setattr(admin_check_module, "get_current_user_id", lambda: user_id)
    if spring_client is not None:
        monkeypatch.setattr(
            admin_check_module, "get_spring_client", Mock(return_value=spring_client)
        )


# 管理员角色放行请求并按当前用户 id 查询角色
def test_grants_access_for_admin_role(monkeypatch: pytest.MonkeyPatch) -> None:
    spring_client, get_users_by_ids = _build_spring_client(
        [{"id": 7, "role": Messages.ROLE_ADMIN}]
    )
    _patch_dependencies(monkeypatch, user_id=7, spring_client=spring_client)

    @requireAdmin
    async def endpoint(*, article_id: int) -> int:
        return article_id

    assert asyncio.run(endpoint(article_id=117)) == 117
    get_users_by_ids.assert_awaited_once_with([7])


# 普通用户角色被拒返回 403 无管理员权限
def test_denies_regular_user_role(monkeypatch: pytest.MonkeyPatch) -> None:
    spring_client, _ = _build_spring_client([{"id": 7, "role": Messages.ROLE_USER}])
    _patch_dependencies(monkeypatch, user_id=7, spring_client=spring_client)

    @requireAdmin
    async def endpoint() -> str:
        return "ok"

    with pytest.raises(BusinessException) as error:
        asyncio.run(endpoint())

    assert error.value.status_code == HttpCode.FORBIDDEN
    assert error.value.error == ErrorCodes.ERROR_USER_NO_ADMIN_PERMISSION


# 查询结果为空或角色缺失时按普通用户拒绝返回 403
@pytest.mark.parametrize("users", [[], [{"id": 7}], [{"id": 7, "role": ""}]])
def test_missing_role_falls_back_to_regular_user(
    monkeypatch: pytest.MonkeyPatch, users: list[dict[str, object]]
) -> None:
    spring_client, _ = _build_spring_client(users)
    _patch_dependencies(monkeypatch, user_id=7, spring_client=spring_client)

    @requireAdmin
    async def endpoint() -> str:
        return "ok"

    with pytest.raises(BusinessException) as error:
        asyncio.run(endpoint())

    assert error.value.status_code == HttpCode.FORBIDDEN
    assert error.value.error == ErrorCodes.ERROR_USER_NO_ADMIN_PERMISSION


# 未登录或用户 id 为 0 时返回 401 且不查询管理员角色
@pytest.mark.parametrize("user_id", [None, 0])
def test_missing_current_user_is_rejected(
    monkeypatch: pytest.MonkeyPatch, user_id: int | None
) -> None:
    spring_client, get_users_by_ids = _build_spring_client([])
    _patch_dependencies(monkeypatch, user_id=user_id, spring_client=spring_client)

    @requireAdmin
    async def endpoint() -> str:
        return "ok"

    with pytest.raises(BusinessException) as error:
        asyncio.run(endpoint())

    assert error.value.status_code == HttpCode.UNAUTHORIZED
    assert error.value.error == ErrorCodes.ERROR_USER_NOT_LOGIN
    get_users_by_ids.assert_not_awaited()


# 管理员校验服务异常时 fail-closed 返回 403
def test_admin_lookup_failure_is_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    spring_client = Mock()
    spring_client.get_users_by_ids = AsyncMock(side_effect=RuntimeError("unavailable"))
    _patch_dependencies(monkeypatch, user_id=7, spring_client=spring_client)

    @requireAdmin
    async def endpoint() -> str:
        return "ok"

    with pytest.raises(BusinessException) as error:
        asyncio.run(endpoint())

    assert error.value.status_code == HttpCode.FORBIDDEN
    assert error.value.error == ErrorCodes.ERROR_PERMISSION_CHECK_FAILED


# 接口自身业务异常穿透装饰器保持原状态码与错误码
def test_business_exception_from_endpoint_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spring_client, _ = _build_spring_client([{"id": 7, "role": Messages.ROLE_ADMIN}])
    _patch_dependencies(monkeypatch, user_id=7, spring_client=spring_client)

    @requireAdmin
    async def endpoint() -> str:
        raise BusinessException(
            "文章不存在", HttpCode.NOT_FOUND, ErrorCodes.ERROR_ARTICLE_NOT_FOUND
        )

    with pytest.raises(BusinessException) as error:
        asyncio.run(endpoint())

    assert error.value.status_code == HttpCode.NOT_FOUND
    assert error.value.error == ErrorCodes.ERROR_ARTICLE_NOT_FOUND
