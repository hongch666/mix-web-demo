"""UserPermissionManager 权限判定的单元测试"""

from unittest.mock import AsyncMock, Mock

import pytest

from app.core.constants import Messages
from app.internal.agents import userPermissionManager as upm_module
from app.internal.agents.toolScope import (
    clear_tool_scope,
    get_tool_scope,
    set_tool_scope,
)
from app.internal.agents.userPermissionManager import (
    UserPermissionManager,
    get_user_permission_manager,
)


@pytest.fixture(autouse=True)
def _clear_scope() -> None:
    clear_tool_scope()
    yield
    clear_tool_scope()


def _manager(users: list[dict] | None = None, side_effect: Exception | None = None):
    client = AsyncMock()
    if side_effect is not None:
        client.get_users_by_ids.side_effect = side_effect
    else:
        client.get_users_by_ids.return_value = users if users is not None else []
    return UserPermissionManager(spring_client=client), client


# 远程客户端返回 admin 角色时按用户 ID 查询并返回该角色
@pytest.mark.anyio
async def test_get_user_role_returns_role_from_remote_client() -> None:
    manager, client = _manager([{"role": "admin"}])

    assert await manager.get_user_role_async(7, Mock()) == "admin"
    client.get_users_by_ids.assert_awaited_once_with([7])


# 远程未返回该用户时回退为默认 user 角色
@pytest.mark.anyio
async def test_get_user_role_falls_back_to_default_when_user_missing() -> None:
    manager, _ = _manager([])

    assert await manager.get_user_role_async(7, Mock()) == Messages.ROLE_USER


# 远程调用抛异常时 fail-closed 回退为默认 user 角色
@pytest.mark.anyio
async def test_get_user_role_falls_back_to_default_on_remote_failure() -> None:
    manager, _ = _manager(side_effect=RuntimeError("spring unavailable"))

    assert await manager.get_user_role_async(7, Mock()) == Messages.ROLE_USER


# 仅 admin 角色判定为管理员，user 角色返回 False
@pytest.mark.anyio
async def test_is_admin_true_only_for_admin_role(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _ = _manager([{"role": Messages.ROLE_ADMIN}])
    assert await manager.is_admin_async(1, Mock()) is True

    user_manager, _ = _manager([{"role": Messages.ROLE_USER}])
    assert await user_manager.is_admin_async(2, Mock()) is False


# admin 角色写入作用域时标记管理员且不限制行级范围
def test_apply_tool_scope_marks_admin_without_row_limit() -> None:
    manager, _ = _manager()

    manager.apply_tool_scope(1, Messages.ROLE_ADMIN)

    scope = get_tool_scope()
    assert scope is not None
    assert scope.user_id == 1
    assert scope.is_admin is True


# 普通用户写入作用域时限定到自身 user_id 且非管理员
def test_apply_tool_scope_restricts_non_admin_to_own_rows() -> None:
    manager, _ = _manager()

    manager.apply_tool_scope(9, Messages.ROLE_USER)

    scope = get_tool_scope()
    assert scope is not None
    assert scope.user_id == 9
    assert scope.is_admin is False


# 匿名user_id 为 0 使用 sql 工具被拒绝并清空已写入的作用域
@pytest.mark.anyio
async def test_anonymous_sql_access_is_rejected_and_scope_cleared() -> None:
    manager, _ = _manager()
    set_tool_scope(9, False)

    allowed, message = await manager.can_use_tool_async(0, Mock(), "sql")

    assert allowed is False
    assert message == Messages.TOOL_ACCESS_LOGIN_REQUIRED("数据库查询")
    assert get_tool_scope() is None


# 匿名使用 mongodb 工具时错误文案指向日志查询
@pytest.mark.anyio
async def test_anonymous_mongodb_access_reports_log_tool_name() -> None:
    manager, _ = _manager()

    allowed, message = await manager.can_use_tool_async(0, Mock(), "mongodb")

    assert allowed is False
    assert message == Messages.TOOL_ACCESS_LOGIN_REQUIRED("日志查询")


# 普通用户通过 sql 工具授权后作用域限定为本人且非管理员
@pytest.mark.anyio
async def test_non_admin_access_grants_scoped_permission() -> None:
    manager, client = _manager([{"role": Messages.ROLE_USER}])

    allowed, message = await manager.can_use_tool_async(7, Mock(), "sql")

    assert (allowed, message) == (True, "")
    client.get_users_by_ids.assert_awaited_once_with([7])
    scope = get_tool_scope()
    assert scope is not None
    assert scope.user_id == 7
    assert scope.is_admin is False


# 传入 admin 角色时直接授权且跳过远程角色查询
@pytest.mark.anyio
async def test_admin_access_grants_unscoped_permission_and_skips_role_lookup() -> None:
    manager, client = _manager()

    allowed, message = await manager.can_use_tool_async(
        1, Mock(), "mongodb", role="admin"
    )

    assert (allowed, message) == (True, "")
    client.get_users_by_ids.assert_not_awaited()
    scope = get_tool_scope()
    assert scope is not None
    assert scope.is_admin is True


# can_access 系列按 sql 与 mongodb 类型委派 can_use_tool_async
@pytest.mark.anyio
async def test_can_access_helpers_delegate_to_sql_and_mongodb_tool_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _ = _manager()
    can_use = AsyncMock(return_value=(True, ""))
    monkeypatch.setattr(manager, "can_use_tool_async", can_use)

    assert await manager.can_access_sql_tools_async(7, Mock(), "问题", role="user") == (
        True,
        "",
    )
    assert can_use.await_args.args[2] == "sql"

    can_use.reset_mock()
    await manager.can_access_mongodb_logs_async(7, Mock(), "问题", role="user")
    assert can_use.await_args.args[2] == "mongodb"


# 数据库查询权限校验固定使用 sql 工具类型
@pytest.mark.anyio
async def test_validate_database_query_permission_uses_sql_tool_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _ = _manager()
    can_use = AsyncMock(return_value=(True, ""))
    monkeypatch.setattr(manager, "can_use_tool_async", can_use)

    assert await manager.validate_database_query_permission_async(7, Mock()) == (
        True,
        "",
    )
    assert can_use.await_args.args[2] == "sql"


# 权限管理器工厂清缓存前后返回同一单例且注入 Spring 客户端
def test_get_user_permission_manager_returns_cached_singleton(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = object()
    monkeypatch.setattr(upm_module, "get_spring_client", lambda: fake_client)
    get_user_permission_manager.cache_clear()
    try:
        first = get_user_permission_manager()
        second = get_user_permission_manager()
    finally:
        get_user_permission_manager.cache_clear()

    assert first is second
    assert first._spring_client is fake_client
