import asyncio
import importlib
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.auth import build_admin_checker
from app.core.constants import Messages

admin_checker_module = importlib.import_module("app.core.auth.adminChecker")


def _build_spring_client(users: list[dict[str, object]]) -> tuple[Mock, AsyncMock]:
    get_users_by_ids = AsyncMock(return_value=users)
    spring_client = Mock()
    spring_client.get_users_by_ids = get_users_by_ids
    return spring_client, get_users_by_ids


# 管理员角色返回 True 并按传入用户 id 查询角色
def test_returns_true_for_admin_role() -> None:
    spring_client, get_users_by_ids = _build_spring_client(
        [{"id": 7, "role": Messages.ROLE_ADMIN}]
    )
    checker = build_admin_checker(spring_client)

    assert asyncio.run(checker(7)) is True
    get_users_by_ids.assert_awaited_once_with([7])


# 普通用户角色返回 False
def test_returns_false_for_regular_user_role() -> None:
    spring_client, _ = _build_spring_client([{"id": 7, "role": Messages.ROLE_USER}])
    checker = build_admin_checker(spring_client)

    assert asyncio.run(checker(7)) is False


# 查询结果为空或角色缺失时回退普通用户返回 False
@pytest.mark.parametrize(
    "users", [[], [{"id": 7}], [{"id": 7, "role": ""}], [{"id": 7, "role": None}]]
)
def test_missing_role_falls_back_to_regular_user(
    users: list[dict[str, object]],
) -> None:
    spring_client, _ = _build_spring_client(users)
    checker = build_admin_checker(spring_client)

    assert asyncio.run(checker(7)) is False


# 查询异常时记录日志并原样抛出，降级策略由调用方决定
def test_lookup_failure_is_logged_and_reraised(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(admin_checker_module, "Logger", Mock())
    spring_client = Mock()
    spring_client.get_users_by_ids = AsyncMock(side_effect=RuntimeError("unavailable"))
    checker = build_admin_checker(spring_client)

    with pytest.raises(RuntimeError, match="unavailable"):
        asyncio.run(checker(7))
