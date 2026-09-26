import importlib
from unittest.mock import MagicMock

import pytest

gemini_module = importlib.import_module(
    "app.internal.services.llm.extend.geminiService"
)
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


# Gemini 服务按配置填充模型名与超时并启用结构化输出
def test_gemini_service_maps_config_to_llm_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = _patch_llm_stack(
        monkeypatch,
        {
            "api_key": "unit-test-value",
            "base_url": "https://llm.local/v1",
            "gemini_model_name": "gemini-2.0-flash",
            "timeout": "21",
        },
    )

    service = gemini_module.GeminiService(MagicMock(), spring_client=MagicMock())

    assert service.service_name == "Gemini"
    assert service.config_section == "closeai"
    assert service.model_config_key == "gemini_model_name"
    assert service.model_name == "gemini-2.0-flash"
    assert service.use_structured_output is True
    assert service._timeout == 21
    assert service.llm is fake_client.return_value
    assert fake_client.call_args.kwargs["model"] == "gemini-2.0-flash"


# 未显式传入 spring_client 时回退使用共享单例
def test_gemini_service_falls_back_to_shared_spring_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_llm_stack(
        monkeypatch, {"api_key": "k", "base_url": "u", "gemini_model_name": "m"}
    )
    sentinel = MagicMock(name="spring-client")
    monkeypatch.setattr(
        gemini_module, "get_spring_client", MagicMock(return_value=sentinel)
    )

    service = gemini_module.GeminiService(MagicMock())

    assert service._spring_client is sentinel


# get_gemini_service 对相同参数返回同一缓存实例并注入客户端
def test_gemini_service_factory_returns_cached_singleton(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_llm_stack(
        monkeypatch, {"api_key": "k", "base_url": "u", "gemini_model_name": "m"}
    )
    mapper = MagicMock(name="mapper")
    spring = MagicMock(name="spring")

    first = gemini_module.get_gemini_service(mapper, spring)
    second = gemini_module.get_gemini_service(mapper, spring)

    assert first is second
    assert first._spring_client is spring
