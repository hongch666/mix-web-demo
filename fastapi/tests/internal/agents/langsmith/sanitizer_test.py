"""LangSmith 脱敏器规则的单元测试"""

import pytest

from app.core.constants import Messages, Scripts
from app.internal.agents.langsmith import sanitizer as sanitizer_module
from app.internal.agents.langsmith.sanitizer import (
    _is_sensitive_key,
    _sanitize_dict,
    _sanitize_list,
    _sanitize_string,
    sanitize_metadata,
    sanitize_tool_input,
    sanitize_tool_output,
    sanitize_user_id,
)


# 凭据类键名识别为敏感、业务字段识别为非敏感
@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("api_key", True),
        ("API-KEY", True),
        ("password", True),
        ("access_token", True),
        ("Authorization", True),
        ("credential", True),
        ("dsn", True),
        ("title", False),
        ("views", False),
        ("conversation_id", False),
    ],
)
def test_is_sensitive_key_detects_credential_fields(key: str, expected: bool) -> None:
    assert _is_sensitive_key(key) is expected


# 同一用户 ID 加盐哈希结果稳定、以 u_ 开头且不可反推原值
def test_sanitize_user_id_is_stable_and_not_reversible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LANGSMITH_USER_HASH_KEY", "unit-test-hmac-key")
    monkeypatch.setattr(sanitizer_module, "_user_hash_hmac_key", None)

    first = sanitize_user_id("1001")
    monkeypatch.setattr(sanitizer_module, "_user_hash_hmac_key", None)
    second = sanitize_user_id("1001")

    assert first == second
    assert first.startswith("u_")
    assert len(first) == 18
    assert "1001" not in first


# 空用户 ID 脱敏返回 anonymous
def test_sanitize_user_id_returns_anonymous_for_empty() -> None:
    assert sanitize_user_id("") == "anonymous"


# 字符串脱敏掩码邮箱与手机号并移除邮箱域名
def test_sanitize_string_masks_email_and_phone() -> None:
    masked = _sanitize_string("联系 alice@example.com 或 13812345678")

    assert "alice@***" in masked
    assert "138****5678" in masked
    assert "example.com" not in masked


# 超长字符串被截断到上限并追加截断提示
def test_sanitize_string_truncates_over_max_length() -> None:
    value = "a" * (Scripts.SANITIZER_MAX_STRING_LENGTH + 100)

    result = _sanitize_string(value)

    assert (
        result
        == "a" * Scripts.SANITIZER_MAX_STRING_LENGTH
        + Messages.SANITIZED_TEXT_TRUNCATED(len(value))
    )


# metadata 为 None 时脱敏返回 None
def test_sanitize_metadata_returns_none_for_none() -> None:
    assert sanitize_metadata(None) is None


# 敏感键值被替换为已脱敏标记、普通键保留
def test_sanitize_metadata_masks_sensitive_keys() -> None:
    result = sanitize_metadata({"api_key": "value", "title": "标题"})

    assert result == {"api_key": "***已脱敏***", "title": "标题"}


# 嵌套字典内的敏感键同样被脱敏
def test_sanitize_metadata_recurses_into_nested_dicts() -> None:
    result = sanitize_metadata({"outer": {"password": "x", "count": 1}})

    assert result == {"outer": {"password": "***已脱敏***", "count": 1}}


# 超长列表被截断并在末尾追加截断提示
def test_sanitize_metadata_truncates_long_lists() -> None:
    result = sanitize_metadata({"items": list(range(15))})

    assert result is not None
    items = result["items"]
    assert items[-1] == Messages.SANITIZED_LIST_TRUNCATED(15)
    assert len(items) == Scripts.SANITIZER_MAX_LIST_LENGTH + 1


# 未知类型值在 metadata 中被转为字符串
def test_sanitize_metadata_stringifies_unknown_types() -> None:
    result = sanitize_metadata({"obj": object()})

    assert result is not None
    assert isinstance(result["obj"], str)


# 超过最大深度时字典返回深度截断标记
def test_sanitize_dict_marks_max_depth() -> None:
    result = _sanitize_dict({"child": {}}, depth=Scripts.SANITIZER_MAX_DICT_DEPTH + 1)

    assert result == {
        "_truncated": Messages.SANITIZED_MAX_DEPTH(Scripts.SANITIZER_MAX_DICT_DEPTH)
    }


# 超过最大深度时列表返回深度截断标记
def test_sanitize_list_marks_max_depth() -> None:
    result = _sanitize_list([1, 2], depth=Scripts.SANITIZER_MAX_DICT_DEPTH + 1)

    assert result == [
        Messages.SANITIZED_LIST_MAX_DEPTH(Scripts.SANITIZER_MAX_DICT_DEPTH)
    ]


# 工具输入按字符串、字典、空字典与其它类型分别处理
def test_sanitize_tool_input_handles_string_dict_and_other_types() -> None:
    assert sanitize_tool_input("a@b.com") == "a@***"
    assert "已脱敏" in sanitize_tool_input({"password": "x"})
    assert sanitize_tool_input({}) == "[工具输入已隐藏]"
    assert sanitize_tool_input(123) == Messages.SANITIZED_TOOL_INPUT_HIDDEN("int")


# 工具输出返回长度摘要并在超长时截断
def test_sanitize_tool_output_reports_length_and_truncation() -> None:
    assert sanitize_tool_output(None) == Messages.SANITIZED_TOOL_OUTPUT_LENGTH(0)
    assert sanitize_tool_output("ok") == Messages.SANITIZED_TOOL_OUTPUT_LENGTH(2)

    long_text = "x" * (Scripts.SANITIZER_MAX_STRING_LENGTH + 1)
    assert sanitize_tool_output(long_text) == Messages.SANITIZED_OUTPUT_TRUNCATED(
        len(long_text), long_text[:100]
    )
