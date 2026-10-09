from typing import Any

import pytest

from app.core.auth import is_memory_user, normalize_user_id


# 整数字符串与带空白的输入统一转换为整数，其余输入归一为空
@pytest.mark.parametrize(
    ("user_id", "expected"),
    [
        (7, 7),
        ("7", 7),
        (" 7 ", 7),
        (0, 0),
        ("-1", -1),
        (None, None),
        ("", None),
        ("   ", None),
        ("abc", None),
        ("7.5", None),
    ],
)
def test_normalize_user_id_converts_only_integer_input(
    user_id: Any, expected: Any
) -> None:
    assert normalize_user_id(user_id) == expected


# 系统调用身份不承载聊天记忆，只有真实用户才读写记忆
@pytest.mark.parametrize(
    ("user_id", "expected"),
    [
        ("7", True),
        (1, True),
        (" 7 ", True),
        ("0", False),
        (0, False),
        ("-1", False),
        ("abc", False),
        ("", False),
        (None, False),
    ],
)
def test_is_memory_user_only_accepts_positive_user_id(
    user_id: Any, expected: bool
) -> None:
    assert is_memory_user(user_id) is expected
