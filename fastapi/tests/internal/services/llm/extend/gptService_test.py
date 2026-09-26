import importlib
from unittest.mock import MagicMock

import pytest

gpt_module = importlib.import_module("app.internal.services.llm.extend.gptService")
base_module = importlib.import_module("app.internal.services.llm.baseAIService")


def _patch_llm_stack(monkeypatch: pytest.MonkeyPatch, service_cfg: dict) -> MagicMock:
    """替换配置读取、ChatOpenAI 与 agent 初始化，隔离外部依赖"""

    def fake_load_config(section=None, key=None):  # noqa: ANN001
        if section == "agent":
            return {"closeai": service_cfg}
        return {}

    monkeypatch.setattr(base_module, "load_config", fake_load_config)
    fake_client = MagicMock(name="ChatOpenAI")
    monkeypatch.setattr(base_module, "ChatOpenAI", fake_client)
    monkeypatch.setattr(
        base_module.BaseAiService,
        "_initialize_agent_stack",
        lambda self, max_iterations=5: None,
    )
    return fake_client


# GPT 服务按配置填充模型名、超时与 reasoning_effort 并创建客户端
def test_gpt_service_maps_config_to_llm_client(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = _patch_llm_stack(
        monkeypatch,
        {
            "api_key": "unit-test-value",
            "base_url": "https://llm.local/v1",
            "gpt_model_name": "gpt-4o-mini",
            "timeout": "42",
            "gpt_reasoning_effort": "low",
        },
    )

    service = gpt_module.GptService(MagicMock(), spring_client=MagicMock())

    assert service.service_name == "GPT"
    assert service.config_section == "closeai"
    assert service.model_config_key == "gpt_model_name"
    assert service.model_name == "gpt-4o-mini"
    assert service.use_structured_output is True
    assert service._timeout == 42
    assert service.llm is fake_client.return_value

    kwargs = fake_client.call_args.kwargs
    assert kwargs["model"] == "gpt-4o-mini"
    assert kwargs["base_url"] == "https://llm.local/v1"
    assert kwargs["timeout"] == 42
    assert kwargs["reasoning_effort"] == "low"


# 未配置 gpt_reasoning_effort 时不向客户端下发该参数
def test_gpt_service_omits_reasoning_effort_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = _patch_llm_stack(
        monkeypatch,
        {
            "api_key": "unit-test-value",
            "base_url": "https://llm.local/v1",
            "gpt_model_name": "gpt-4o-mini",
        },
    )

    gpt_module.GptService(MagicMock(), spring_client=MagicMock())

    assert "reasoning_effort" not in fake_client.call_args.kwargs


# 未显式传入 spring_client 时回退使用共享单例
def test_gpt_service_falls_back_to_shared_spring_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_llm_stack(
        monkeypatch, {"api_key": "k", "base_url": "u", "gpt_model_name": "m"}
    )
    sentinel = MagicMock(name="spring-client")
    monkeypatch.setattr(
        gpt_module, "get_spring_client", MagicMock(return_value=sentinel)
    )

    service = gpt_module.GptService(MagicMock())

    assert service._spring_client is sentinel


# get_gpt_service 对相同参数返回同一缓存实例并注入客户端
def test_gpt_service_factory_returns_cached_singleton(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_llm_stack(
        monkeypatch, {"api_key": "k", "base_url": "u", "gpt_model_name": "m"}
    )
    mapper = MagicMock(name="mapper")
    spring = MagicMock(name="spring")

    first = gpt_module.get_gpt_service(mapper, spring)
    second = gpt_module.get_gpt_service(mapper, spring)

    assert first is second
    assert first._spring_client is spring
