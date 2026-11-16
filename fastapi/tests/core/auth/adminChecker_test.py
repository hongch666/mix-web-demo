import asyncio
import importlib
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.auth import build_admin_checker

admin_checker_module = importlib.import_module("app.core.auth.adminChecker")


def _build_spring_client(is_admin: bool) -> tuple[Mock, AsyncMock]:
    is_admin_user = AsyncMock(return_value=is_admin)
    spring_client = Mock()
    spring_client.is_admin_user = is_admin_user
    return spring_client, is_admin_user


# 管理员返回 True 并按传入用户 id 查询
def test_returns_true_for_admin() -> None:
    spring_client, is_admin_user = _build_spring_client(True)
    checker = build_admin_checker(spring_client)

    assert asyncio.run(checker(7)) is True
    is_admin_user.assert_awaited_once_with(7)


# 非管理员返回 False
def test_returns_false_for_regular_user() -> None:
    spring_client, is_admin_user = _build_spring_client(False)
    checker = build_admin_checker(spring_client)

    assert asyncio.run(checker(7)) is False
    is_admin_user.assert_awaited_once_with(7)


# 查询异常时记录日志并原样抛出，降级策略由调用方决定
def test_lookup_failure_is_logged_and_reraised(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(admin_checker_module, "Logger", Mock())
    spring_client = Mock()
    spring_client.is_admin_user = AsyncMock(side_effect=RuntimeError("unavailable"))
    checker = build_admin_checker(spring_client)

    with pytest.raises(RuntimeError, match="unavailable"):
        asyncio.run(checker(7))
