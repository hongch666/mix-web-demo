from collections.abc import Generator
from unittest.mock import AsyncMock

import httpx
import pytest

from app.common.middleware.contextMiddleware import (
    session_id_ctx_var,
    token_ctx_var,
    user_id_ctx_var,
    username_ctx_var,
)
from app.core.client import client as client_module
from app.core.errors import BusinessException


@pytest.fixture(autouse=True)
def reset_client_state(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    client_module._SERVICE_BREAKERS.clear()
    monkeypatch.setattr(client_module, "wait_exponential", lambda **_: lambda _: 0)
    yield
    client_module._SERVICE_BREAKERS.clear()


def test_merge_headers_propagates_context_and_allows_explicit_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeTokenUtil:
        def generate_internal_token(self, user_id: int, service_name: str) -> str:
            assert user_id == 7
            assert service_name == "fastapi"
            return "internal-token"

    monkeypatch.setattr(client_module, "InternalTokenUtil", FakeTokenUtil)
    monkeypatch.setattr(
        client_module,
        "load_config",
        lambda section: {"service_name": "fastapi"},
    )
    tokens = [
        (user_id_ctx_var, user_id_ctx_var.set(7)),
        (username_ctx_var, username_ctx_var.set("alice")),
        (session_id_ctx_var, session_id_ctx_var.set("session-1")),
        (token_ctx_var, token_ctx_var.set("access-token")),
    ]
    try:
        headers = client_module._merge_headers({"X-Username": "override"})
    finally:
        for variable, token in reversed(tokens):
            variable.reset(token)

    assert headers == {
        "X-User-Id": "7",
        "X-Username": "override",
        "X-Session-Id": "session-1",
        "Authorization": "Bearer access-token",
        "X-Internal-Token": "Bearer internal-token",
    }


def test_internal_token_uses_system_user_for_anonymous_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeTokenUtil:
        def generate_internal_token(self, user_id: int, service_name: str) -> str:
            captured.update(user_id=user_id, service_name=service_name)
            return "system-token"

    monkeypatch.setattr(client_module, "InternalTokenUtil", FakeTokenUtil)
    monkeypatch.setattr(
        client_module,
        "load_config",
        lambda section: {"service_name": "fastapi"},
    )

    assert client_module._build_internal_token_header("") == {
        "X-Internal-Token": "Bearer system-token"
    }
    assert captured == {"user_id": -1, "service_name": "fastapi"}


@pytest.mark.anyio
async def test_call_with_client_retries_503_then_returns_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx.Response(503, request=request, json={"message": "busy"})
        return httpx.Response(
            200, request=request, json={"code": 200, "data": {"id": 1}}
        )

    monkeypatch.setattr(
        client_module,
        "_resolve_service_url",
        AsyncMock(return_value="http://service.local/resource"),
    )
    breaker = client_module.SimpleCircuitBreaker(5, 30)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        result = await client_module._call_with_client(
            http_client,
            "spring",
            "/resource",
            "GET",
            {},
            None,
            None,
            None,
            3,
            breaker,
            1,
        )

    assert result["data"] == {"id": 1}
    assert attempts == 3
    assert breaker.failure_count == 0


@pytest.mark.anyio
@pytest.mark.parametrize("status_code", [400, 401, 403, 404])
async def test_call_with_client_does_not_retry_4xx(
    status_code: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(status_code, request=request, json={"message": "invalid"})

    monkeypatch.setattr(
        client_module,
        "_resolve_service_url",
        AsyncMock(return_value="http://service.local/resource"),
    )
    breaker = client_module.SimpleCircuitBreaker(5, 30)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(BusinessException) as caught:
            await client_module._call_with_client(
                http_client,
                "spring",
                "/resource",
                "GET",
                {},
                None,
                None,
                None,
                3,
                breaker,
                1,
            )

    assert caught.value.status_code == 502
    assert attempts == 1
    assert breaker.failure_count == 1


@pytest.mark.anyio
async def test_open_circuit_fails_fast_without_http_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_mock = AsyncMock()
    http_client = AsyncMock(spec=httpx.AsyncClient)
    http_client.request = request_mock
    breaker = client_module.SimpleCircuitBreaker(1, 30)
    breaker.record_failure()

    with pytest.raises(BusinessException) as caught:
        await client_module._call_with_client(
            http_client,
            "spring",
            "/resource",
            "GET",
            {},
            None,
            None,
            None,
            3,
            breaker,
            1,
        )

    assert caught.value.status_code == 503
    request_mock.assert_not_awaited()


@pytest.mark.anyio
async def test_business_error_is_not_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            200, request=request, json={"code": 400, "msg": "invalid"}
        )

    monkeypatch.setattr(
        client_module,
        "_resolve_service_url",
        AsyncMock(return_value="http://service.local/resource"),
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(BusinessException):
            await client_module._call_with_client(
                http_client,
                "spring",
                "/resource",
                "GET",
                {},
                None,
                None,
                None,
                3,
                client_module.SimpleCircuitBreaker(5, 30),
                1,
            )

    assert attempts == 1
