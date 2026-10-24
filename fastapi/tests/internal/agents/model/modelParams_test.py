"""模型参数能力判定（temperature 与结构化输出）的单元测试"""

import pytest

from app.internal.agents.model.modelParams import (
    DEFAULT_STRUCTURED_OUTPUT_UNSUPPORTED_PREFIXES,
    DEFAULT_TEMPERATURE_UNSUPPORTED_PREFIXES,
    parse_model_prefixes,
    supports_structured_output,
    supports_temperature,
)


# 前缀表按配置值解析，缺省、空白与非法值回落调用方传入的兜底前缀
@pytest.mark.parametrize(
    ("value", "fallback", "expected"),
    [
        (None, ("claude",), ("claude",)),
        ("", ("claude",), ("claude",)),
        (" , ", ("claude",), ("claude",)),
        (123, ("claude",), ("claude",)),
        (" Claude , gemini ", ("claude",), ("claude", "gemini")),
        ("claude,CLAUDE", ("fallback",), ("claude",)),
        (["claude", " glm "], ("fallback",), ("claude", "glm")),
    ],
)
def test_parse_model_prefixes(
    value: object, fallback: tuple[str, ...], expected: tuple[str, ...]
) -> None:
    assert parse_model_prefixes(value, fallback) == expected


# 命中前缀的模型不下发 temperature，其它模型与空模型名按支持处理
@pytest.mark.parametrize(
    ("model_name", "prefixes", "expected"),
    [
        ("claude-haiku-5-5", None, False),
        ("CLAUDE-OPUS-5", None, False),
        ("gpt-6-luna", None, True),
        ("glm-5.3-flash", "glm,gemini", False),
        ("gpt-6-luna", "glm,gemini", True),
        ("claude-haiku-5-5", "deepseek,glm", True),
        ("", "claude", True),
    ],
)
def test_supports_temperature(
    model_name: str, prefixes: object, expected: bool
) -> None:
    assert supports_temperature(model_name, prefixes) is expected


# 命中前缀的模型不启用 json_schema 结构化输出，默认兜底 deepseek 与 glm
@pytest.mark.parametrize(
    ("model_name", "prefixes", "expected"),
    [
        ("deepseek-v4.1-flash", None, False),
        ("DeepSeek-chat", None, False),
        ("glm-5.3-flash", None, False),
        ("gpt-6-luna", None, True),
        ("deepseek-v4.1-flash", "claude", True),
        ("claude-haiku-5-5", "deepseek,glm", True),
        ("", "deepseek", True),
    ],
)
def test_supports_structured_output(
    model_name: str, prefixes: object, expected: bool
) -> None:
    assert supports_structured_output(model_name, prefixes) is expected


# 两类能力的兜底前缀相互独立，互不影响判定
def test_capability_fallbacks_are_independent() -> None:
    assert supports_temperature("claude-haiku-5-5") is False
    assert supports_structured_output("claude-haiku-5-5") is True
    assert supports_temperature("deepseek-v4.1-flash") is True
    assert supports_structured_output("deepseek-v4.1-flash") is False
    assert DEFAULT_TEMPERATURE_UNSUPPORTED_PREFIXES == ("claude",)
    assert DEFAULT_STRUCTURED_OUTPUT_UNSUPPORTED_PREFIXES == ("deepseek", "glm")
