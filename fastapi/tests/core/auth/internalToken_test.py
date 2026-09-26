import os
from collections.abc import Generator
from datetime import datetime, timedelta, UTC

import jwt
import pytest

from app.core.auth import InternalTokenUtil
from app.core.errors import BusinessException

TEST_SECRET = "unit-test-secret-32-bytes-long-key"


@pytest.fixture(autouse=True)
def reset_internal_token_util() -> Generator[None, None, None]:
    InternalTokenUtil._instance = None
    InternalTokenUtil._secret = TEST_SECRET
    InternalTokenUtil._expiration = 60_000
    InternalTokenUtil._initialized = True
    yield
    InternalTokenUtil._instance = None
    InternalTokenUtil._initialized = False
    InternalTokenUtil._secret = None
    InternalTokenUtil._expiration = None


# 生成的内部令牌校验通过并能提取用户 id 与服务名
def test_generate_and_validate_internal_token_claims() -> None:
    InternalTokenUtil._secret = os.getenv("INTERNAL_TOKEN_SECRET") or TEST_SECRET
    token_util = InternalTokenUtil()
    token = token_util.generate_internal_token(10001, "fastapi")
    claims = token_util.validate_internal_token(token)

    print(f"生成的内部Token: {token}")

    assert claims["userId"] == 10001
    assert claims["serviceName"] == "fastapi"
    assert claims["tokenType"] == "internal"
    assert token_util.extract_user_id(token) == 10001
    assert token_util.extract_service_name(token) == "fastapi"


# 使用其他密钥签名的令牌校验失败返回 401
def test_rejects_token_signed_with_another_secret() -> None:
    token = jwt.encode(
        {
            "userId": 10001,
            "serviceName": "fastapi",
            "tokenType": "internal",
            "exp": datetime.now(UTC) + timedelta(minutes=1),
        },
        "another-unit-test-secret-with-32-bytes",
        algorithm="HS256",
    )

    with pytest.raises(BusinessException) as error:
        InternalTokenUtil().validate_internal_token(token)

    assert error.value.status_code == 401


# 已过期令牌校验失败返回 401
def test_rejects_expired_token() -> None:
    token = jwt.encode(
        {
            "userId": 10001,
            "serviceName": "fastapi",
            "tokenType": "internal",
            "exp": datetime.now(UTC) - timedelta(seconds=1),
        },
        TEST_SECRET,
        algorithm="HS256",
    )

    with pytest.raises(BusinessException) as error:
        InternalTokenUtil().validate_internal_token(token)

    assert error.value.status_code == 401
