import pytest

from app.core.config import load_config
from app.core.config.config import resolve_env_vars_in_string


def test_resolve_env_vars_in_string_prefers_env_and_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONFIG_TEST_VALUE", "from-env")

    assert resolve_env_vars_in_string("${CONFIG_TEST_VALUE}") == "from-env"
    assert resolve_env_vars_in_string("${CONFIG_TEST_MISSING:fallback}") == "fallback"
    assert resolve_env_vars_in_string("${CONFIG_TEST_MISSING}") == ""
    assert resolve_env_vars_in_string("a-${CONFIG_TEST_VALUE}-b") == "a-from-env-b"


def test_load_config_reads_application_yaml_section_and_key() -> None:
    full_config = load_config()
    assert isinstance(full_config, dict)

    server_config = load_config("server")
    assert isinstance(server_config, dict)
    assert server_config.get("port") is not None
    assert load_config("server", "port") is not None

    assert load_config("not-exist-section") is None
