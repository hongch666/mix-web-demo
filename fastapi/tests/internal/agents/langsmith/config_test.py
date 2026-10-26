"""LangSmith 配置加载的单元测试"""

import pytest

from app.internal.agents.langsmith import config as config_module
from app.internal.agents.langsmith.config import load_langsmith_config


def _raw_config(**overrides: str) -> dict:
    base = {
        "enabled": "true",
        "api_key": "unit-test-key",
        "project": " mix-project ",
        "endpoint": " http://langsmith.local ",
        "workspace_id": "",
        "hide_inputs": "false",
        "hide_outputs": "false",
        "sampling_rate": "0.5",
    }
    base.update(overrides)
    return base


def _patch(monkeypatch: pytest.MonkeyPatch, raw: dict) -> None:
    monkeypatch.setattr(config_module, "load_config", lambda section: raw)


# 原始配置解析后布尔、数值与首尾空白按预期归一化
def test_load_config_parses_and_strips_values(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(monkeypatch, _raw_config())

    config = load_langsmith_config()

    assert config.enabled is True
    assert config.api_key == "unit-test-key"
    assert config.project == "mix-project"
    assert config.endpoint == "http://langsmith.local"
    assert config.workspace_id is None
    assert config.hide_inputs is False
    assert config.hide_outputs is False
    assert config.sampling_rate == 0.5


# api_key 为空时强制关闭 LangSmith 追踪
def test_load_config_forces_disabled_when_api_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch(monkeypatch, _raw_config(api_key=""))

    config = load_langsmith_config()

    assert config.enabled is False


# hide 开关与 workspace_id 按字符串解析为对应类型
def test_load_config_parses_hide_flags_and_workspace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch(
        monkeypatch,
        _raw_config(workspace_id="ws-1", hide_inputs="true", hide_outputs="true"),
    )

    config = load_langsmith_config()

    assert config.workspace_id == "ws-1"
    assert config.hide_inputs is True
    assert config.hide_outputs is True


# enabled 显式为 false 时保持关闭
def test_load_config_respects_explicit_disable(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(monkeypatch, _raw_config(enabled="false"))

    assert load_langsmith_config().enabled is False


# 未显式配置时脱敏长度上限使用默认值
def test_load_config_uses_default_sanitizer_limits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch(monkeypatch, _raw_config())

    config = load_langsmith_config()

    assert config.max_string_length > 0
    assert config.max_list_length > 0
    assert config.max_dict_depth > 0
