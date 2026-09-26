import asyncio
import importlib
from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import Request

from app.common.decorators import requireInternalToken
from app.core.constants import ErrorCodes, HttpCode, Messages
from app.core.errors import BusinessException

internal_token_module = importlib.import_module(
    "app.common.decorators.requireInternalToken"
)


def _make_request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/internal/ping",
            "headers": [],
            "query_string": b"",
            "path_params": {},
        }
    )


def _patch_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    *,
    credential: str | None,
    claims: dict[str, Any] | None = None,
    error: Exception | None = None,
) -> Mock:
    validate = Mock(return_value=claims)
    if error is not None:
        validate = Mock(side_effect=error)
    monkeypatch.setattr(internal_token_module, "Logger", Mock())
    monkeypatch.setattr(
        internal_token_module, "get_current_internal_token", lambda: credential
    )
    monkeypatch.setattr(
        internal_token_module,
        "InternalTokenUtil",
        Mock(return_value=Mock(validate_internal_token=validate)),
    )
    return validate


# 接口未声明 Request 参数时返回 401 内部令牌缺失
def test_rejects_when_request_object_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_dependencies(monkeypatch, credential="internal.jwt")

    @requireInternalToken
    async def endpoint() -> str:
        return "ok"

    with pytest.raises(BusinessException) as error:
        asyncio.run(endpoint())

    assert error.value.status_code == HttpCode.UNAUTHORIZED
    assert error.value.error == ErrorCodes.ERROR_INTERNAL_TOKEN_MISSING


# 内部令牌为空或缺失时返回 401 令牌缺失
@pytest.mark.parametrize("token", [None, ""])
def test_rejects_when_internal_token_missing(
    monkeypatch: pytest.MonkeyPatch, token: str | None
) -> None:
    _patch_dependencies(monkeypatch, credential=token)

    @requireInternalToken
    async def endpoint(request: Request) -> str:
        return "ok"

    with pytest.raises(BusinessException) as error:
        asyncio.run(endpoint(request=_make_request()))

    assert error.value.status_code == HttpCode.UNAUTHORIZED
    assert error.value.error == ErrorCodes.ERROR_INTERNAL_TOKEN_MISSING


# 有效令牌校验通过并把声明写入 request.state
def test_allows_valid_token_and_stores_claims(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    claims = {"userId": 10001, "serviceName": "fastapi"}
    validate = _patch_dependencies(
        monkeypatch, credential="internal.jwt", claims=claims
    )
    request = _make_request()

    @requireInternalToken
    async def endpoint(request: Request, *, payload: int = 0) -> int:
        return payload + 1

    assert asyncio.run(endpoint(request=request, payload=1)) == 2
    validate.assert_called_once_with("internal.jwt")
    assert request.state.internal_token_claims == claims


# 令牌服务名与要求一致时放行请求
def test_allows_token_from_required_service(monkeypatch: pytest.MonkeyPatch) -> None:
    claims = {"userId": -1, "serviceName": "spring"}
    validate = _patch_dependencies(
        monkeypatch, credential="internal.jwt", claims=claims
    )

    @requireInternalToken(required_service_name="spring")
    async def endpoint(request: Request) -> str:
        return "ok"

    assert asyncio.run(endpoint(request=_make_request())) == "ok"
    validate.assert_called_once_with("internal.jwt")


# 令牌服务名不匹配时返回 403 服务不匹配
def test_rejects_token_from_another_service(monkeypatch: pytest.MonkeyPatch) -> None:
    claims = {"userId": 10001, "serviceName": "nestjs"}
    _patch_dependencies(monkeypatch, credential="internal.jwt", claims=claims)

    @requireInternalToken(required_service_name="spring")
    async def endpoint(request: Request) -> str:
        return "ok"

    with pytest.raises(BusinessException) as error:
        asyncio.run(endpoint(request=_make_request()))

    assert error.value.status_code == HttpCode.FORBIDDEN
    assert error.value.error == ErrorCodes.ERROR_INTERNAL_TOKEN_SERVICE_MISMATCH


# 令牌验签抛异常时统一返回 401 无效令牌
def test_invalid_token_is_rejected_as_unauthorized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_dependencies(
        monkeypatch, credential="internal.jwt", error=ValueError("signature mismatch")
    )

    @requireInternalToken()
    async def endpoint(request: Request) -> str:
        return "ok"

    with pytest.raises(BusinessException) as error:
        asyncio.run(endpoint(request=_make_request()))

    assert error.value.status_code == HttpCode.UNAUTHORIZED
    assert error.value.error == ErrorCodes.ERROR_INTERNAL_TOKEN_INVALID


# 校验抛出的业务异常保持原始错误码向上传播
def test_business_exception_from_validation_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expired = BusinessException(
        Messages.INTERNAL_TOKEN_EXPIRED,
        HttpCode.UNAUTHORIZED,
        ErrorCodes.ERROR_INTERNAL_TOKEN_EXPIRED,
    )
    _patch_dependencies(monkeypatch, credential="internal.jwt", error=expired)

    @requireInternalToken
    async def endpoint(request: Request) -> str:
        return "ok"

    with pytest.raises(BusinessException) as error:
        asyncio.run(endpoint(request=_make_request()))

    assert error.value.error == ErrorCodes.ERROR_INTERNAL_TOKEN_EXPIRED


# 接口自身业务异常穿透装饰器保持原状态码与错误码
def test_business_exception_from_endpoint_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    claims = {"userId": 10001, "serviceName": "spring"}
    _patch_dependencies(monkeypatch, credential="internal.jwt", claims=claims)

    @requireInternalToken
    async def endpoint(request: Request) -> str:
        raise BusinessException(
            "文章不存在", HttpCode.NOT_FOUND, ErrorCodes.ERROR_ARTICLE_NOT_FOUND
        )

    with pytest.raises(BusinessException) as error:
        asyncio.run(endpoint(request=_make_request()))

    assert error.value.status_code == HttpCode.NOT_FOUND
    assert error.value.error == ErrorCodes.ERROR_ARTICLE_NOT_FOUND


# 裸用与调用两种装饰形式对同步接口均抛 TypeError
@pytest.mark.parametrize(
    "decorate",
    [
        pytest.param(requireInternalToken, id="bare"),
        pytest.param(requireInternalToken(), id="called"),
    ],
)
def test_rejects_synchronous_endpoint(decorate: Any) -> None:
    def endpoint() -> str:
        return "ok"

    with pytest.raises(TypeError, match=Messages.REQUIRE_INTERNAL_TOKEN_ASYNC_ERROR):
        decorate(endpoint)
