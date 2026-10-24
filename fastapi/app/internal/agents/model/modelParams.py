"""模型参数能力判定

不同厂家的模型对采样参数与响应格式的支持不一致，例如新一代 Claude 已弃用
temperature、DeepSeek 与 GLM 的 OpenAI 兼容接口不支持 json_schema 结构化输出，
命中不支持的能力时接口直接返回 400 invalid_request_error，因此统一按模型名前缀判定

前缀表来自 agent.closeai 下的 temperature_unsupported_prefixes 与
structured_output_unsupported_prefixes 配置，调用方读取配置后传入，
未配置时使用内置兜底前缀，保证默认配置下不会把模型不支持的参数发出去
"""

from collections.abc import Iterable
from typing import Any

# 未配置前缀表时生效的兜底前缀，命中即认为模型不接受 temperature
DEFAULT_TEMPERATURE_UNSUPPORTED_PREFIXES: tuple[str, ...] = ("claude",)

# 未配置前缀表时生效的兜底前缀，命中即认为模型不支持 json_schema 结构化输出
DEFAULT_STRUCTURED_OUTPUT_UNSUPPORTED_PREFIXES: tuple[str, ...] = ("deepseek", "glm")


def parse_model_prefixes(value: Any, fallback: tuple[str, ...]) -> tuple[str, ...]:
    """把配置值解析为模型名前缀元组

    支持逗号分隔字符串与序列两种写法，解析结果统一转小写并去空白、去重

    Args:
        value: 配置值
        fallback: 配置缺省或解析结果为空时使用的兜底前缀

    Returns:
        tuple[str, ...]: 保持配置顺序的前缀元组
    """
    if value is None:
        return fallback
    if isinstance(value, str):
        items: Iterable[Any] = value.split(",")
    elif isinstance(value, Iterable):
        items = value
    else:
        return fallback

    prefixes: list[str] = []
    for item in items:
        text: str = str(item).strip().lower()
        if text and text not in prefixes:
            prefixes.append(text)
    return tuple(prefixes) or fallback


def _matches_unsupported_prefix(
    model_name: str, unsupported_prefixes: Any, fallback: tuple[str, ...]
) -> bool:
    """判断模型名是否命中不支持某能力的前缀表，模型名为空时按不命中处理"""
    normalized: str = str(model_name or "").strip().lower()
    if not normalized:
        return False
    return normalized.startswith(parse_model_prefixes(unsupported_prefixes, fallback))


def supports_temperature(model_name: str, unsupported_prefixes: Any = None) -> bool:
    """判断模型是否仍接受 temperature 参数

    Args:
        model_name: 模型名称，为空时按接受处理
        unsupported_prefixes: 已弃用该参数的模型名前缀配置

    Returns:
        bool: 可以下发 temperature 时返回 True
    """
    return not _matches_unsupported_prefix(
        model_name, unsupported_prefixes, DEFAULT_TEMPERATURE_UNSUPPORTED_PREFIXES
    )


def supports_structured_output(
    model_name: str, unsupported_prefixes: Any = None
) -> bool:
    """判断模型是否支持 json_schema 结构化输出

    部分模型的 OpenAI 兼容接口会返回 response_format 类型不可用，
    命中前缀时关闭意图识别的结构化输出，直接走文本匹配链路

    Args:
        model_name: 模型名称，为空时按支持处理
        unsupported_prefixes: 不支持结构化输出的模型名前缀配置

    Returns:
        bool: 支持结构化输出时返回 True
    """
    return not _matches_unsupported_prefix(
        model_name,
        unsupported_prefixes,
        DEFAULT_STRUCTURED_OUTPUT_UNSUPPORTED_PREFIXES,
    )
