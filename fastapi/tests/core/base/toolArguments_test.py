"""工具入参类型解析的单元测试"""

from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from app.core.base import JsonArrayArgument, JsonObjectArgument, parse_json_string


class _ObjectModel(BaseModel):
    """承载 JsonObjectArgument 字段的测试模型"""

    payload: JsonObjectArgument


class _ArrayModel(BaseModel):
    """承载 JsonArrayArgument 字段的测试模型"""

    payload: JsonArrayArgument


# 非字符串入参原样返回，不对已经解析好的容器二次处理
@pytest.mark.parametrize("value", [{"a": 1}, [1, 2], 7, 1.5, None, True])
def test_parse_json_string_keeps_non_string_value(value: Any) -> None:
    assert parse_json_string(value) == value


# 合法 JSON 字符串还原成字典或列表
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ('{"page": 1}', {"page": 1}),
        ('[{"$match": {"status": 1}}]', [{"$match": {"status": 1}}]),
        ("{}", {}),
        ("[]", []),
    ],
)
def test_parse_json_string_decodes_json_text(value: str, expected: Any) -> None:
    assert parse_json_string(value) == expected


# 非法 JSON 文本原样返回字符串，交由字段校验给出可读错误
@pytest.mark.parametrize("value", ["{bad", "not-json", ""])
def test_parse_json_string_keeps_invalid_json_text(value: str) -> None:
    assert parse_json_string(value) == value


# JsonObjectArgument 接受模型传来的 JSON 字符串写法
def test_json_object_argument_decodes_json_text() -> None:
    model = _ObjectModel(payload='{"page": 1, "size": 20}')

    assert model.payload == {"page": 1, "size": 20}


# JsonObjectArgument 校验失败于 JSON 数组文本，避免数组被当成键值对象
def test_json_object_argument_rejects_json_array_text() -> None:
    with pytest.raises(ValidationError):
        _ObjectModel(payload="[1, 2]")


# JsonObjectArgument 对无法解析的文本抛出校验错误而非静默通过
def test_json_object_argument_rejects_invalid_json_text() -> None:
    with pytest.raises(ValidationError):
        _ObjectModel(payload="{bad")


# JsonArrayArgument 接受模型传来的 JSON 字符串写法
def test_json_array_argument_decodes_json_text() -> None:
    model = _ArrayModel(payload='[{"$match": {"status": 1}}]')

    assert model.payload == [{"$match": {"status": 1}}]


# JsonArrayArgument 校验失败于 JSON 对象文本，避免字典被当成数组
def test_json_array_argument_rejects_json_object_text() -> None:
    with pytest.raises(ValidationError):
        _ArrayModel(payload='{"a": 1}')


# 已经是目标容器的入参保持原值，不做多余转换
@pytest.mark.parametrize(
    ("model_class", "value"),
    [
        (_ObjectModel, {"a": 1}),
        (_ArrayModel, [1, 2]),
    ],
)
def test_arguments_keep_container_input_intact(
    model_class: type[BaseModel], value: Any
) -> None:
    assert model_class(payload=value).payload == value
