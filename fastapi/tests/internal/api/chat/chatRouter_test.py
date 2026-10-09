import pytest

from app.internal.api.chat.chatRouter import _is_memory_user


# 系统调用身份不写入聊天记忆，只有真实用户才落库
@pytest.mark.parametrize(
    ("actual_user_id", "expected"),
    [
        ("7", True),
        ("1", True),
        ("0", False),
        ("-1", False),
        ("abc", False),
        ("", False),
    ],
)
def test_is_memory_user_only_accepts_positive_user_id(
    actual_user_id: str, expected: bool
) -> None:
    assert _is_memory_user(actual_user_id) is expected
