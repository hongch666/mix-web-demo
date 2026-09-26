import importlib
from unittest.mock import MagicMock

import pytest

glm_module = importlib.import_module("app.internal.services.llm.extend.glmService")
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


# GLM 服务按配置填充模型名并关闭结构化输出
def test_glm_service_maps_config_and_disables_structured_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = _patch_llm_stack(
        monkeypatch,
        {
            "api_key": "unit-test-value",
            "base_url": "https://llm.local/v1",
            "glm_model_name": "glm-4-plus",
            "timeout": "30",
        },
    )

    service = glm_module.GlmService(MagicMock(), spring_client=MagicMock())

    assert service.service_name == "GLM"
    assert service.config_section == "closeai"
    assert service.model_config_key == "glm_model_name"
    assert service.model_name == "glm-4-plus"
    assert service.use_structured_output is False
    assert service.llm is fake_client.return_value
    assert fake_client.call_args.kwargs["model"] == "glm-4-plus"


# GLM 流式选项下发 thinking 开启与低推理强度
def test_glm_service_final_stream_options_enable_thinking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_llm_stack(
        monkeypatch, {"api_key": "k", "base_url": "u", "glm_model_name": "m"}
    )

    service = glm_module.GlmService(MagicMock(), spring_client=MagicMock())

    assert service._final_stream_options() == {
        "extra_body": {"thinking": {"type": "enabled", "reasoning_effort": "low"}}
    }


# 未显式传入 spring_client 时回退使用共享单例
def test_glm_service_falls_back_to_shared_spring_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_llm_stack(
        monkeypatch, {"api_key": "k", "base_url": "u", "glm_model_name": "m"}
    )
    sentinel = MagicMock(name="spring-client")
    monkeypatch.setattr(
        glm_module, "get_spring_client", MagicMock(return_value=sentinel)
    )

    service = glm_module.GlmService(MagicMock())

    assert service._spring_client is sentinel


# get_glm_service 对相同参数返回同一缓存实例并注入客户端
def test_glm_service_factory_returns_cached_singleton(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_llm_stack(
        monkeypatch, {"api_key": "k", "base_url": "u", "glm_model_name": "m"}
    )
    mapper = MagicMock(name="mapper")
    spring = MagicMock(name="spring")

    first = glm_module.get_glm_service(mapper, spring)
    second = glm_module.get_glm_service(mapper, spring)

    assert first is second
    assert first._spring_client is spring
