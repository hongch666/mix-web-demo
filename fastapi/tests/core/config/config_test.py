import pytest

from app.core.config.config import resolve_env_vars_in_string


# 占位符优先取环境变量，缺失时用默认值或空串且支持嵌入文本
def test_resolve_env_vars_in_string_prefers_env_and_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONFIG_TEST_VALUE", "from-env")

    assert resolve_env_vars_in_string("${CONFIG_TEST_VALUE}") == "from-env"
    assert resolve_env_vars_in_string("${CONFIG_TEST_MISSING:fallback}") == "fallback"
    assert resolve_env_vars_in_string("${CONFIG_TEST_MISSING}") == ""
    assert resolve_env_vars_in_string("a-${CONFIG_TEST_VALUE}-b") == "a-from-env-b"
