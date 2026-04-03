import os
from typing import Generator

import pytest
from app.core.auth.internalToken import InternalTokenUtil


@pytest.fixture(autouse=True)
def reset_internal_token_util() -> Generator[None, None, None]:
    InternalTokenUtil._instance = None
    InternalTokenUtil._initialized = False
    InternalTokenUtil._secret = None
    InternalTokenUtil._expiration = None
    yield
    InternalTokenUtil._instance = None
    InternalTokenUtil._initialized = False
    InternalTokenUtil._secret = None
    InternalTokenUtil._expiration = None


def test_generate_internal_token() -> None:
    internal_token_util = InternalTokenUtil()
    token = internal_token_util.generate_internal_token(10001, "fastapi")
    print(f"生成的内部Token: {token}")

    assert token


def test_validate_internal_token() -> None:
    token = os.getenv("INTERNAL_TOKEN_TEST_TOKEN")
    assert token, "环境变量 INTERNAL_TOKEN_TEST_TOKEN 不能为空"
    internal_token_util = InternalTokenUtil()
    claims = internal_token_util.validate_internal_token(token)

    assert claims
