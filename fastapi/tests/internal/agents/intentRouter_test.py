"""IntentRouter 意图识别与权限校验的单元测试"""

from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from langchain_core.runnables import Runnable

from app.core.constants import Messages
from app.internal.agents import intentRouter as intent_router_module
from app.internal.agents.intentRouter import IntentRouter, StructuredIntent


class _FakeRunnable(Runnable):
    """可控结果的 Runnable，用于替换 LLM 与结构化输出链"""

    def __init__(self, result: Any = None, error: Exception | None = None) -> None:
        self._result = result
        self._error = error

    def invoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any:
        if self._error is not None:
            raise self._error
        return self._result

    async def ainvoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any:
        if self._error is not None:
            raise self._error
        return self._result


class _FakeLLM(_FakeRunnable):
    """模拟 LangChain LLM，支持文本输出与结构化输出两条链路"""

    def __init__(
        self,
        text_result: Any = "article_search",
        text_error: Exception | None = None,
        structured_result: Any = None,
        structured_error: Exception | None = None,
        structured_supported: bool = True,
    ) -> None:
        super().__init__(result=text_result, error=text_error)
        self._structured_result = structured_result
        self._structured_error = structured_error
        self._structured_supported = structured_supported
        self.structured_calls = 0

    def with_structured_output(self, schema: Any, **kwargs: Any) -> _FakeRunnable:
        self.structured_calls += 1
        if not self._structured_supported:
            raise RuntimeError("with_structured_output 不可用")
        return _FakeRunnable(
            result=self._structured_result, error=self._structured_error
        )


class _FakePermissionManager:
    """权限管理器替身，便于观察工具作用域与权限分支"""

    def __init__(
        self,
        role: str = "user",
        sql_result: tuple[bool, str] = (True, ""),
        mongodb_result: tuple[bool, str] = (True, ""),
    ) -> None:
        self.role = role
        self.get_user_role_async = AsyncMock(return_value=role)
        self.apply_tool_scope = Mock()
        self.can_access_sql_tools_async = AsyncMock(return_value=sql_result)
        self.can_access_mongodb_logs_async = AsyncMock(return_value=mongodb_result)


def _router_with_intent(intent: str, resolution: str = "structured") -> IntentRouter:
    router = IntentRouter(llm=_FakeLLM(), use_structured_output=False)
    router.route_async = AsyncMock(return_value=(intent, resolution))  # type: ignore[method-assign]
    return router


def _patch_permission_manager(
    monkeypatch: pytest.MonkeyPatch, manager: _FakePermissionManager
) -> None:
    monkeypatch.setattr(
        intent_router_module, "get_user_permission_manager", lambda: manager
    )


# 结构化输出可用时返回结构化意图且只绑定一次结构化链
@pytest.mark.anyio
async def test_route_async_returns_structured_intent_when_available() -> None:
    llm = _FakeLLM(
        structured_result=StructuredIntent(type="knowledge_query", confidence=0.9)
    )
    router = IntentRouter(llm=llm)

    assert await router.route_async("有哪些相关文章") == (
        "knowledge_query",
        "structured",
    )
    assert llm.structured_calls == 1


# 结构化结果为纯文本时降级为 text_fallback 并解析文本意图
@pytest.mark.anyio
async def test_route_async_degrades_when_structured_returns_plain_text() -> None:
    llm = _FakeLLM(structured_result="数据库相关")
    router = IntentRouter(llm=llm)

    assert await router.route_async("查数据库") == ("database_query", "text_fallback")


# 结构化链抛异常时回退到文本匹配解析意图
@pytest.mark.anyio
async def test_route_async_falls_back_to_text_match_on_structured_failure() -> None:
    llm = _FakeLLM(
        text_result="知识图谱",
        structured_error=RuntimeError("structured boom"),
    )
    router = IntentRouter(llm=llm)

    assert await router.route_async("推荐关系") == ("knowledge_query", "text_fallback")


# 文本匹配也失败时返回 article_search 默认兜底
@pytest.mark.anyio
async def test_route_async_returns_default_fallback_when_text_match_fails() -> None:
    llm = _FakeLLM(text_error=RuntimeError("llm down"))
    router = IntentRouter(llm=llm, use_structured_output=False)

    assert await router.route_async("任意问题") == (
        "article_search",
        "default_fallback",
    )


# 关闭结构化输出时不绑定结构化链
def test_structured_output_disabled_skips_structured_binding() -> None:
    llm = _FakeLLM()
    router = IntentRouter(llm=llm, use_structured_output=False)

    assert router._use_structured_output is False
    assert llm.structured_calls == 0


# 结构化输出绑定失败时隔离异常并关闭该能力
def test_structured_output_binding_failure_is_isolated() -> None:
    llm = _FakeLLM(structured_supported=False)

    router = IntentRouter(llm=llm)

    assert router._use_structured_output is False
    assert llm.structured_calls == 1


# set_user_context 覆盖路由器的用户 ID 与数据库会话
def test_set_user_context_overwrites_identity_and_session() -> None:
    router = IntentRouter(llm=_FakeLLM(), use_structured_output=False)
    session = Mock()

    router.set_user_context(11, session)

    assert router.user_id == 11
    assert router.db is session


# 文本意图解析按关键词映射到对应意图
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("database", "database_query"),
        ("查询数据库", "database_query"),
        ("article", "article_search"),
        ("SEARCH", "article_search"),
        ("日志分析", "log_analysis"),
        ("knowledge", "knowledge_query"),
        ("图谱推荐", "knowledge_query"),
        ("general chat", "general_chat"),
        ("完全无关", "article_search"),
    ],
)
def test_resolve_text_intent_maps_keywords(text: str, expected: str) -> None:
    assert IntentRouter._resolve_text_intent(text) == expected


# 未登录请求 database_query 意图被拒绝并返回无权限消息
@pytest.mark.anyio
async def test_database_query_without_login_is_rejected() -> None:
    router = _router_with_intent("database_query")

    result = await router.route_with_permission_check_async("查一下表")

    assert result == (
        "database_query",
        False,
        Messages.INTENT_ROUTER_NO_PERMISSION_ERROR,
        "structured",
    )


# 未登录请求 log_analysis 意图被拒绝并保留解析方式
@pytest.mark.anyio
async def test_log_analysis_without_login_is_rejected() -> None:
    router = _router_with_intent("log_analysis", "text_fallback")

    result = await router.route_with_permission_check_async("看日志")

    assert result == (
        "log_analysis",
        False,
        Messages.INTENT_ROUTER_NO_PERMISSION_ERROR,
        "text_fallback",
    )


# 未登录请求 article_search 意图仍放行
@pytest.mark.anyio
async def test_article_search_without_login_is_allowed() -> None:
    router = _router_with_intent("article_search")

    assert await router.route_with_permission_check_async("找文章") == (
        "article_search",
        True,
        "",
        "structured",
    )


# 危险自然语言写请求在权限校验前被拦截且不查 SQL 权限
@pytest.mark.anyio
async def test_dangerous_write_request_blocks_database_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        Messages, "is_dangerous_nl_request", staticmethod(lambda question: True)
    )
    manager = _FakePermissionManager()
    _patch_permission_manager(monkeypatch, manager)
    router = _router_with_intent("database_query")

    result = await router.route_with_permission_check_async(
        "删除所有用户", user_id=7, db=Mock()
    )

    assert result == (
        "database_query",
        False,
        Messages.SQL_NATURAL_LANGUAGE_WRITE_BLOCK_MESSAGE,
        "structured",
    )
    manager.can_access_sql_tools_async.assert_not_awaited()


# 数据库意图写入工具作用域并按角色校验 SQL 权限
@pytest.mark.anyio
async def test_database_query_applies_scope_and_checks_sql_permission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _FakePermissionManager(role="user", sql_result=(True, ""))
    _patch_permission_manager(monkeypatch, manager)
    router = _router_with_intent("database_query")
    session = Mock()

    result = await router.route_with_permission_check_async(
        "查询统计", user_id=7, db=session
    )

    assert result == ("database_query", True, "", "structured")
    manager.get_user_role_async.assert_awaited_once_with(7, session)
    manager.apply_tool_scope.assert_called_once_with(7, "user")
    assert manager.can_access_sql_tools_async.await_args.kwargs["role"] == "user"
    assert manager.can_access_sql_tools_async.await_args.args[:2] == (7, session)


# SQL 权限校验被拒时返回拒绝消息
@pytest.mark.anyio
async def test_database_query_denied_returns_permission_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _FakePermissionManager(sql_result=(False, "禁止访问"))
    _patch_permission_manager(monkeypatch, manager)
    router = _router_with_intent("database_query")

    result = await router.route_with_permission_check_async(
        "查询统计", user_id=7, db=Mock()
    )

    assert result == ("database_query", False, "禁止访问", "structured")


# knowledge_query 意图放行且不触发工具权限校验
@pytest.mark.anyio
async def test_knowledge_query_is_allowed_without_tool_permission_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _FakePermissionManager()
    _patch_permission_manager(monkeypatch, manager)
    router = _router_with_intent("knowledge_query")

    result = await router.route_with_permission_check_async(
        "推荐相关文章", user_id=7, db=Mock()
    )

    assert result == ("knowledge_query", True, "", "structured")
    manager.can_access_sql_tools_async.assert_not_awaited()
    manager.can_access_mongodb_logs_async.assert_not_awaited()


# log_analysis 意图按 MongoDB 日志权限校验
@pytest.mark.anyio
async def test_log_analysis_checks_mongodb_permission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _FakePermissionManager(mongodb_result=(False, "无日志权限"))
    _patch_permission_manager(monkeypatch, manager)
    router = _router_with_intent("log_analysis")

    result = await router.route_with_permission_check_async(
        "分析日志", user_id=7, db=Mock()
    )

    assert result == ("log_analysis", False, "无日志权限", "structured")
    manager.can_access_mongodb_logs_async.assert_awaited_once()


# 请求传入的身份覆盖路由器默认用户与会话
@pytest.mark.anyio
async def test_request_supplied_identity_overrides_router_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _FakePermissionManager()
    _patch_permission_manager(monkeypatch, manager)
    router = _router_with_intent("article_search")
    session = Mock()

    await router.route_with_permission_check_async("找文章", user_id=3, db=session)

    assert router.user_id == 3
    assert router.db is session
    manager.apply_tool_scope.assert_called_once_with(3, "user")
