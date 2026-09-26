"""FastapiSqlTool 本地直连 SQL 工具的单元测试"""

import json
from typing import Any

import pytest

from app.core.constants import Messages
from app.internal.agents.toolScope import clear_tool_scope, set_tool_scope
from app.internal.agents.tools import fastapiSqlTool as sql_module
from app.internal.agents.tools.fastapiSqlTool import FastapiSqlTool


class _FakeResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def mappings(self) -> "_FakeResult":
        return self

    def all(self) -> list[dict[str, Any]]:
        return self._rows


class _FakeSession:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self.executed: tuple[Any, Any] | None = None

    async def execute(self, statement: Any, params: Any) -> _FakeResult:
        self.executed = (statement, params)
        return _FakeResult(self._rows)


def _fake_get_db(session: _FakeSession):
    async def _generator():
        yield session

    return _generator


@pytest.fixture(autouse=True)
def _clear_scope() -> None:
    clear_tool_scope()
    yield
    clear_tool_scope()


# 空语句直接返回查询为空消息
@pytest.mark.anyio
async def test_execute_query_rejects_empty_statement() -> None:
    assert await FastapiSqlTool().execute_query("   ") == Messages.SQL_TOOL_QUERY_EMPTY


# 删除类写语句被只读白名单拦截
@pytest.mark.anyio
async def test_execute_query_rejects_write_statement() -> None:
    result = await FastapiSqlTool().execute_query("DELETE FROM ai_history LIMIT 10")

    assert result == Messages.SQL_TOOL_FORBIDDEN_STATEMENT


# 白名单外的表被拒绝并回显表名
@pytest.mark.anyio
async def test_execute_query_rejects_table_outside_whitelist() -> None:
    result = await FastapiSqlTool().execute_query("SELECT * FROM other_table LIMIT 10")

    assert result == Messages.SQL_TOOL_TABLE_NOT_IN_WHITELIST("other_table")


# 缺少 LIMIT 子句时被拒绝
@pytest.mark.anyio
async def test_execute_query_requires_limit_clause() -> None:
    result = await FastapiSqlTool().execute_query("SELECT * FROM ai_history")

    assert result == Messages.SQL_TOOL_LIMIT_REQUIRED


# LIMIT 超过上限时被拒绝
@pytest.mark.anyio
async def test_execute_query_rejects_limit_above_maximum() -> None:
    result = await FastapiSqlTool().execute_query("SELECT * FROM ai_history LIMIT 101")

    assert result == Messages.SQL_TOOL_LIMIT_EXCEEDED


# 非管理员在触碰数据库前被拒绝且不执行查询
@pytest.mark.anyio
async def test_execute_query_denies_non_admin_before_touching_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_tool_scope(user_id=7, is_admin=False)
    session = _FakeSession([])
    monkeypatch.setattr(sql_module, "get_db", _fake_get_db(session))

    result = await FastapiSqlTool().execute_query(
        "SELECT id FROM ai_history WHERE user_id = :user_id LIMIT 10",
        {"user_id": 7},
    )

    assert result == Messages.NON_ADMIN_ARBITRARY_QUERY_FORBIDDEN
    assert session.executed is None


# 管理员查询返回列名、行数据与行数的结构化结果
@pytest.mark.anyio
async def test_execute_query_returns_structured_rows_for_admin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_tool_scope(user_id=1, is_admin=True)
    session = _FakeSession([{"id": 1, "title": "标题"}])
    monkeypatch.setattr(sql_module, "get_db", _fake_get_db(session))

    result = await FastapiSqlTool().execute_query(
        "SELECT id, title FROM ai_history LIMIT 10"
    )

    assert json.loads(result) == {
        "columns": ["id", "title"],
        "rows": [[1, "标题"]],
        "rowCount": 1,
    }
    assert session.executed is not None
    assert session.executed[1] == {}


# 管理员查询无结果时返回空结果集结构
@pytest.mark.anyio
async def test_execute_query_returns_empty_result_set_for_admin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_tool_scope(user_id=1, is_admin=True)
    monkeypatch.setattr(sql_module, "get_db", _fake_get_db(_FakeSession([])))

    result = await FastapiSqlTool().execute_query("SELECT id FROM ai_history LIMIT 5")

    assert json.loads(result) == {"columns": [], "rows": [], "rowCount": 0}


# 会话获取失败时包装为查询失败消息
@pytest.mark.anyio
async def test_execute_query_wraps_session_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_tool_scope(user_id=1, is_admin=True)

    def _broken_get_db():
        raise RuntimeError("db down")

    monkeypatch.setattr(sql_module, "get_db", _broken_get_db)

    result = await FastapiSqlTool().execute_query("SELECT id FROM ai_history LIMIT 5")

    assert result == Messages.SQL_TOOL_QUERY_FAILED("FastAPI", RuntimeError("db down"))


# 指定表返回含列信息的单表结构描述
@pytest.mark.anyio
async def test_get_tables_returns_single_table_schema() -> None:
    result = await FastapiSqlTool().get_tables("ai_history")

    payload = json.loads(result)
    assert payload["table"] == "ai_history"
    assert isinstance(payload["columns"], list)


# 未知表返回不在白名单消息
@pytest.mark.anyio
async def test_get_tables_rejects_unknown_table() -> None:
    result = await FastapiSqlTool().get_tables("unknown_table")

    assert result == Messages.SQL_TOOL_TABLE_NOT_IN_WHITELIST("unknown_table")


# 空表名时列出全部白名单表
@pytest.mark.anyio
async def test_get_tables_lists_all_whitelisted_tables() -> None:
    result = await FastapiSqlTool().get_tables("")

    payload = json.loads(result)
    assert {item["table"] for item in payload} == set(
        Messages.SQL_TOOL_FASTAPI_TABLE_WHITELIST
    )


# 暴露的表查询与查询工具名称与常量一致
def test_get_langchain_tools_exposes_table_and_query_tools() -> None:
    tools = FastapiSqlTool().get_langchain_tools()

    assert [tool.name for tool in tools] == [
        Messages.SQL_TOOL_FASTAPI_TABLE_TOOL_NAME,
        Messages.SQL_TOOL_FASTAPI_QUERY_TOOL_NAME,
    ]
