from collections.abc import Generator
from pathlib import Path

import pytest

from app.core.config import clear_config_cache, config as config_module, load_config
from app.core.config.config import resolve_env_vars_in_string


@pytest.fixture(autouse=True)
def _reset_config_cache() -> Generator[None, None, None]:
    """每个用例前后清空配置缓存，避免单例缓存串到其它用例"""
    clear_config_cache()
    yield
    clear_config_cache()


# 占位符优先取环境变量，缺失时用默认值或空串且支持嵌入文本
def test_resolve_env_vars_in_string_prefers_env_and_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONFIG_TEST_VALUE", "from-env")

    assert resolve_env_vars_in_string("${CONFIG_TEST_VALUE}") == "from-env"
    assert resolve_env_vars_in_string("${CONFIG_TEST_MISSING:fallback}") == "fallback"
    assert resolve_env_vars_in_string("${CONFIG_TEST_MISSING}") == ""
    assert resolve_env_vars_in_string("a-${CONFIG_TEST_VALUE}-b") == "a-from-env-b"


@pytest.fixture
def config_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """把配置定位指向临时文件，测试不读取仓库真实配置"""
    config_path = tmp_path / "application.yaml"
    config_path.write_text("logs:\n  path: /tmp/logs\n  file_level: INFO\n", "utf-8")
    monkeypatch.setattr(config_module, "_resolve_config_path", lambda: config_path)
    return config_path


# 同一进程内配置只读盘解析一次，文件后续变化在清空缓存前不影响结果
def test_load_config_returns_cached_document(config_file: Path) -> None:
    first = load_config("logs")
    config_file.write_text("logs:\n  path: /changed\n", "utf-8")

    second = load_config("logs")

    assert second is first
    assert second["path"] == "/tmp/logs"


# 清空缓存后重新读盘，能拿到文件最新内容
def test_clear_config_cache_reloads_document(config_file: Path) -> None:
    assert load_config("logs", "path") == "/tmp/logs"
    config_file.write_text("logs:\n  path: /changed\n", "utf-8")

    clear_config_cache()

    assert load_config("logs", "path") == "/changed"


# 不存在的配置段按 key 取值返回 None，不抛异常
def test_load_config_returns_none_for_missing_section(config_file: Path) -> None:
    assert load_config("missing", "key") is None
    assert load_config("missing") is None


# 未指定 section 时返回整份配置
def test_load_config_returns_full_document(config_file: Path) -> None:
    assert load_config()["logs"]["file_level"] == "INFO"
