import pytest

from app.core.config.config import resolve_env_vars_in_string


def test_resolve_env_vars_in_string_prefers_env_and_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONFIG_TEST_VALUE", "from-env")

    assert resolve_env_vars_in_string("${CONFIG_TEST_VALUE}") == "from-env"
    assert resolve_env_vars_in_string("${CONFIG_TEST_MISSING:fallback}") == "fallback"
    assert resolve_env_vars_in_string("${CONFIG_TEST_MISSING}") == ""
    assert resolve_env_vars_in_string("a-${CONFIG_TEST_VALUE}-b") == "a-from-env-b"
