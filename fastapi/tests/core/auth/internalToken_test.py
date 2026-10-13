import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Optional

import jwt
import pytest
from dotenv import dotenv_values

from app.core.auth import InternalTokenUtil
from app.core.errors import BusinessException

TEST_SECRET = "unit-test-secret-32-bytes-long-key"


def resolve_internal_token_secret() -> str:
    """内部令牌测试密钥：优先进程环境变量，其次 .env 配置，最后回退固定假密钥"""
    environment_secret: str = os.getenv("INTERNAL_TOKEN_SECRET", "").strip()
    if environment_secret:
        return environment_secret
    return _read_secret_from_env_files() or TEST_SECRET


def _read_secret_from_env_files() -> Optional[str]:
    """读取 .env 中的 INTERNAL_TOKEN_SECRET，先查服务目录再查仓库根目录"""
    for candidate in (Path.cwd() / ".env", Path.cwd().parent / ".env"):
        if not candidate.exists():
            continue
        value: Optional[str] = dotenv_values(candidate).get("INTERNAL_TOKEN_SECRET")
        if value and value.strip():
            return value.strip()
    return None


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
    # 输出到控制台的令牌需用 .env 配置的真实密钥签发，未配置时回退固定假密钥
    InternalTokenUtil._secret = resolve_internal_token_secret()
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
