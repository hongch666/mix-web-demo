from app.core.constants import Messages
from app.internal.agents.toolScope import (
    clear_tool_scope,
    enforce_mongodb_row_scope,
    enforce_sql_row_scope,
    set_tool_scope,
)


def test_non_admin_cannot_bypass_sql_scope_with_nested_query() -> None:
    set_tool_scope(user_id=7, is_admin=False)

    try:
        denial = enforce_sql_row_scope(
            "SELECT * FROM ai_history WHERE user_id = :user_id OR 1 = 1",
            {"user_id": 7},
        )
    finally:
        clear_tool_scope()

    assert denial == Messages.NON_ADMIN_ARBITRARY_QUERY_FORBIDDEN


def test_non_admin_cannot_bypass_mongodb_scope_with_or_filter() -> None:
    set_tool_scope(user_id=7, is_admin=False)

    try:
        denial = enforce_mongodb_row_scope(
            {"$or": [{"userId": 7}, {"userId": {"$ne": 7}}]}
        )
    finally:
        clear_tool_scope()

    assert denial == Messages.NON_ADMIN_ARBITRARY_QUERY_FORBIDDEN


def test_admin_can_use_structured_query_tools() -> None:
    set_tool_scope(user_id=1, is_admin=True)

    try:
        assert enforce_sql_row_scope("SELECT * FROM users", None) is None
        assert enforce_mongodb_row_scope({}) is None
    finally:
        clear_tool_scope()
