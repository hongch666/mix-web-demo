import importlib
import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.prompts import ChatPromptTemplate

from app.core.constants import Messages, Prompts
from app.internal.agents import AgentToolFactories
from app.internal.services.llm.baseAIService import (
    BaseAiService,
    get_agent_prompt,
    initialize_ai_tools,
)

base_module = importlib.import_module("app.internal.services.llm.baseAIService")


# ===== 测试替身 =====


class _FakeResponse:
    def __init__(self, content: object) -> None:
        self.content = content


class _FakeChunk:
    def __init__(self, content: object) -> None:
        self.content = content


class _FakeAction:
    def __init__(self, tool: str, tool_input: str) -> None:
        self.tool = tool
        self.tool_input = tool_input


class _FakeHistory:
    def __init__(self, ask: str, reply: str) -> None:
        self.ask = ask
        self.reply = reply


class _FakeStreamingLLM:
    """最小可用 LLM 替身，覆盖 ainvoke 与 astream 两条路径"""

    def __init__(
        self,
        chunks: list[object] | None = None,
        invoke_result: object | None = None,
        invoke_error: Exception | None = None,
        stream_error: Exception | None = None,
    ) -> None:
        self._chunks = chunks or []
        self._invoke_result = invoke_result
        self._invoke_error = invoke_error
        self._stream_error = stream_error
        self.invoke_calls: list[dict[str, object]] = []
        self.stream_calls: list[dict[str, object]] = []

    async def ainvoke(self, messages, config=None, **kwargs):  # noqa: ANN001
        self.invoke_calls.append(
            {"messages": messages, "config": config, "kwargs": kwargs}
        )
        if self._invoke_error is not None:
            raise self._invoke_error
        return self._invoke_result

    async def astream(self, messages, config=None, **kwargs):  # noqa: ANN001
        self.stream_calls.append(
            {"messages": messages, "config": config, "kwargs": kwargs}
        )
        if self._stream_error is not None:
            raise self._stream_error
        for chunk in self._chunks:
            yield chunk


class _FakeAgentExecutor:
    def __init__(
        self,
        events: list[dict] | None = None,
        stream_error: Exception | None = None,
        invoke_result: dict | None = None,
    ) -> None:
        self._events = events or []
        self._stream_error = stream_error
        self._invoke_result = invoke_result
        self.astream_events_calls: list[dict[str, object]] = []

    async def astream_events(self, payload, config=None, version="v2"):  # noqa: ANN001
        self.astream_events_calls.append(
            {"payload": payload, "config": config, "version": version}
        )
        if self._stream_error is not None:
            raise self._stream_error
        for event in self._events:
            yield event

    async def ainvoke(self, payload, config=None):  # noqa: ANN001
        return self._invoke_result


class _FakeIntentRouter:
    def __init__(
        self,
        route_result: tuple | None = None,
        permission_result: tuple | None = None,
    ) -> None:
        self.route_async = AsyncMock(
            return_value=route_result or ("general_chat", "default_fallback")
        )
        self.route_with_permission_check_async = AsyncMock(
            return_value=permission_result
            or ("general_chat", True, "", "default_fallback")
        )


def _make_service(**overrides) -> BaseAiService:
    """绕过 __init__ 的可控构造，避免真实读取配置与创建 LLM 客户端"""
    service = BaseAiService.__new__(BaseAiService)
    service.ai_history_mapper = AsyncMock()
    service.service_name = "AI"
    service.config_section = "closeai"
    service.model_config_key = "model_name"
    service.temperature = 0.7
    service.use_structured_output = True
    service._tool_factories = None
    service.llm = None
    service.agent = None
    service.agent_executor = None
    service.intent_router = None
    service.all_tools = []
    service.model_name = ""
    service._api_key = ""
    service._base_url = ""
    service._timeout = 30
    for name, value in overrides.items():
        setattr(service, name, value)
    return service


async def _collect_frames(stream: AsyncGenerator[dict, None]) -> list[dict]:
    return [frame async for frame in stream]


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
        BaseAiService,
        "_initialize_agent_stack",
        lambda self, max_iterations=5: None,
    )
    return fake_client


# ===== 静态/纯函数逻辑 =====


# HTTPS_PROXY 的 socks 方案改写为 socks5，其它代理环境变量不变
def test_normalize_proxy_env_rewrites_socks_scheme(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HTTPS_PROXY", "socks://proxy.local:1080")
    monkeypatch.setenv("NO_PROXY", "unchanged.local")

    BaseAiService._normalize_proxy_env()

    assert os.environ["HTTPS_PROXY"] == "socks5://proxy.local:1080"
    assert os.environ["NO_PROXY"] == "unchanged.local"


# None、字符串、数字、内容块列表与嵌套对象均提取为纯文本
@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (None, ""),
        ("hello", "hello"),
        (123, "123"),
        (["a", {"type": "text", "text": "b"}, {"type": "image"}], "ab"),
        (_FakeResponse("nested"), "nested"),
    ],
)
def test_extract_message_content_handles_supported_shapes(
    content, expected: str
) -> None:
    assert BaseAiService._extract_message_content(content) == expected


# content 为空时回退读取 additional_kwargs 中的 text 字段
def test_extract_message_content_falls_back_to_additional_kwargs() -> None:
    class _EmptyContent:
        content = ""
        additional_kwargs = {"text": "from-kwargs"}

    assert BaseAiService._extract_message_content(_EmptyContent()) == "from-kwargs"


# 仅接受正整数形式的 user_id，其余输入统一归一化为 None
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, None),
        ("   ", None),
        ("abc", None),
        ("3.5", None),
        ("42", 42),
        (7, 7),
    ],
)
def test_normalize_user_id(raw, expected: int | None) -> None:
    service = _make_service()
    assert service._normalize_user_id(raw) == expected


# API Key、配额、限流、超时等错误分别映射为对应提示文案
@pytest.mark.parametrize(
    ("error_message", "expected"),
    [
        ("Invalid API key provided", Messages.LLM_INVALID_API_KEY("AI")),
        ("quota exceeded", Messages.LLM_QUOTA_EXCEEDED("AI")),
        ("rate limit reached", Messages.LLM_RATE_LIMIT_EXCEEDED("AI")),
        ("request timeout", Messages.REQUEST_TIMEOUT_ERROR),
        ("unexpected boom", Messages.LLM_SERVICE_ERROR("AI", "unexpected boom")),
    ],
)
def test_resolve_service_error_message_maps_known_errors(
    error_message: str, expected: str
) -> None:
    service = _make_service()
    assert service._resolve_service_error_message(error_message) == expected


# 按模型键前缀读取 reasoning_effort 并去除首尾空白
def test_build_llm_client_options_reads_reasoning_effort_by_prefix() -> None:
    service = _make_service(model_config_key="gpt_model_name")
    assert service._build_llm_client_options({"gpt_reasoning_effort": " high "}) == {
        "reasoning_effort": "high"
    }
    assert service._build_llm_client_options({}) == {}


# GLM 额外下发 thinking 参数，其它模型返回空流式选项
def test_final_stream_options_enable_thinking_only_for_glm() -> None:
    glm = _make_service(service_name="GLM")
    assert glm._final_stream_options() == {
        "extra_body": {"thinking": {"type": "enabled", "reasoning_effort": "low"}}
    }
    assert _make_service(service_name="GPT")._final_stream_options() == {}


# 历史对话只保留最近三轮，空历史返回空字符串
def test_build_chat_context_keeps_last_three_rounds() -> None:
    service = _make_service()
    history = [("q1", "a1"), ("q2", "a2"), ("q3", "a3"), ("q4", "a4")]
    last_three = history[-3:]
    expected = (
        "\n\n历史对话:\n"
        + "\n".join(Messages.CHAT_HISTORY_LINE(h, a) for h, a in last_three)
        + "\n\n"
    )
    assert service._build_chat_context(history) == expected
    assert service._build_chat_context([]) == ""


# 思考文本按执行步骤在前、最终结论在后的顺序拼接
def test_build_complete_thinking_text_orders_steps_then_result() -> None:
    service = _make_service()
    steps = [(_FakeAction("SpringSqlTool", "SELECT 1"), "rows")]
    expected = (
        Messages.AGENT_EXECUTION_PROCESS_HEADER()
        + Messages.AGENT_EXECUTION_STEP(1, "SpringSqlTool", "SELECT 1", "rows")
        + Messages.AGENT_FINAL_RESULT("done")
    )
    assert service._build_complete_thinking_text(steps, "done") == expected
    assert service._build_complete_thinking_text(
        [], "done"
    ) == Messages.AGENT_FINAL_RESULT("done")


# 兜底结果取最后一条非空观察值，全空时返回检索失败文案
def test_build_agent_fallback_result_prefers_last_non_empty_observation() -> None:
    service = _make_service()
    steps = [(_FakeAction("t1", "i1"), ""), (_FakeAction("t2", "i2"), "from-tool")]
    assert service._build_agent_fallback_result(steps) == "from-tool"
    assert (
        service._build_agent_fallback_result([(_FakeAction("t", "i"), "")])
        == Messages.MESSAGE_RETRIEVAL_ERROR
    )


# 重置运行时状态会清空 LLM、agent、意图路由与工具列表
def test_reset_runtime_state_clears_runtime_dependencies() -> None:
    service = _make_service(
        llm=object(),
        agent=object(),
        agent_executor=object(),
        intent_router=object(),
        all_tools=[1, 2],
    )
    service._reset_runtime_state()
    assert service.llm is None
    assert service.agent is None
    assert service.agent_executor is None
    assert service.intent_router is None
    assert service.all_tools == []


# agent 提示词模板仅暴露 input 与 agent_scratchpad 变量
def test_get_agent_prompt_exposes_expected_variables() -> None:
    prompt = get_agent_prompt()
    assert isinstance(prompt, ChatPromptTemplate)
    assert set(prompt.input_variables) == {"input", "agent_scratchpad"}


# ===== 聊天历史加载 =====


# 聊天历史按问答对映射为元组列表并只调用一次 Mapper
@pytest.mark.anyio
async def test_load_chat_history_maps_ask_reply_pairs() -> None:
    mapper = MagicMock()
    mapper.get_all_ai_history_by_userid_async = AsyncMock(
        return_value=[_FakeHistory("q1", "a1"), _FakeHistory("q2", "a2")]
    )
    service = _make_service(ai_history_mapper=mapper)

    result = await service._load_chat_history(7, MagicMock())

    assert result == [("q1", "a1"), ("q2", "a2")]
    mapper.get_all_ai_history_by_userid_async.assert_awaited_once()


# 历史记录查询抛错时返回空列表而不向调用方抛出异常
@pytest.mark.anyio
async def test_load_chat_history_returns_empty_on_failure() -> None:
    mapper = MagicMock()
    mapper.get_all_ai_history_by_userid_async = AsyncMock(
        side_effect=RuntimeError("db down")
    )
    service = _make_service(ai_history_mapper=mapper)

    assert await service._load_chat_history(7, MagicMock()) == []


# ===== 基础对话接口 =====


# 未初始化 LLM 时基础对话返回初始化错误提示
@pytest.mark.anyio
async def test_basic_chat_returns_initialization_error_without_llm() -> None:
    service = _make_service()
    assert await service.basic_chat("你好") == Messages.INITIALIZATION_ERROR


# 基础对话返回模型内容且用户输入作为第二条消息下发
@pytest.mark.anyio
async def test_basic_chat_returns_model_content() -> None:
    llm = _FakeStreamingLLM(invoke_result=_FakeResponse("回答"))
    service = _make_service(llm=llm)

    assert await service.basic_chat("问题") == "回答"
    assert llm.invoke_calls[0]["messages"][1].content == "问题"


# 模型调用异常时基础对话包装为服务错误文案
@pytest.mark.anyio
async def test_basic_chat_wraps_exception() -> None:
    llm = _FakeStreamingLLM(invoke_error=RuntimeError("boom"))
    service = _make_service(llm=llm)

    assert await service.basic_chat("问题") == Messages.CHAT_SERVICE_ERROR("boom")


# 参考对话按待评价文本与权威文本组装参考提示词
@pytest.mark.anyio
async def test_with_reference_chat_builds_reference_prompt() -> None:
    llm = _FakeStreamingLLM(invoke_result=_FakeResponse("评价"))
    service = _make_service(llm=llm)

    result = await service.with_reference_chat("待评价", "权威文本")

    assert result == "评价"
    assert llm.invoke_calls[0]["messages"][1].content == (
        Prompts.REFERENCE_BASED_EVALUATION("待评价", "权威文本")
    )


# 摘要结果按 max_length 截断为指定长度
@pytest.mark.anyio
async def test_summarize_content_truncates_to_max_length() -> None:
    llm = _FakeStreamingLLM(invoke_result=_FakeResponse("x" * 20))
    service = _make_service(llm=llm)

    assert await service.summarize_content("正文", max_length=5) == "xxxxx"


# 未初始化 LLM 时摘要返回初始化错误提示
@pytest.mark.anyio
async def test_summarize_content_returns_initialization_error_without_llm() -> None:
    service = _make_service()
    assert await service.summarize_content("正文") == Messages.INITIALIZATION_ERROR


# ===== simple_chat =====


# 无 agent 时简单对话退化为基础对话且仅调用一次
@pytest.mark.anyio
async def test_simple_chat_falls_back_to_basic_chat_without_agent() -> None:
    llm = _FakeStreamingLLM(invoke_result=_FakeResponse("直答"))
    service = _make_service(llm=llm)

    assert await service.simple_chat("问题") == "直答"
    assert len(llm.invoke_calls) == 1


# 通用意图走直连对话，run_name 为 chat.direct 并携带意图元数据
@pytest.mark.anyio
async def test_simple_chat_general_intent_uses_direct_chat_run_name() -> None:
    llm = _FakeStreamingLLM(invoke_result=_FakeResponse("闲聊答复"))
    service = _make_service(llm=llm, agent_executor=_FakeAgentExecutor())

    result = await service.simple_chat("问题")

    assert result == "闲聊答复"
    config = llm.invoke_calls[0]["config"]
    assert config["run_name"] == "chat.direct"
    assert config["metadata"]["intent"] == "general_chat"
    assert llm.invoke_calls[0]["messages"][0].content == Messages.GENERIC_CHAT_MESSAGE


# 需要工具的意图交由 agent 执行器并返回其输出
@pytest.mark.anyio
async def test_simple_chat_agent_intent_uses_agent_executor() -> None:
    router = _FakeIntentRouter(route_result=("log_analysis", "text_fallback"))
    executor = _FakeAgentExecutor(invoke_result={"output": "最终回答"})
    service = _make_service(
        llm=_FakeStreamingLLM(), intent_router=router, agent_executor=executor
    )

    result = await service.simple_chat("查日志")

    assert result == "最终回答"
    assert router.route_async.await_args.args[0] == "查日志"


# 意图权限校验未通过时直接返回无权限提示内容
@pytest.mark.anyio
async def test_simple_chat_returns_permission_message_when_denied() -> None:
    router = _FakeIntentRouter(
        permission_result=("log_analysis", False, "无权限内容", "structured")
    )
    service = _make_service(
        llm=_FakeStreamingLLM(),
        intent_router=router,
        agent_executor=_FakeAgentExecutor(),
    )

    result = await service.simple_chat("查日志", user_id=5, db=MagicMock())

    assert result == "无权限内容"


# 简单对话异常经错误解析后返回 API Key 无效提示
@pytest.mark.anyio
async def test_simple_chat_wraps_unexpected_error() -> None:
    llm = _FakeStreamingLLM(invoke_error=RuntimeError("invalid api key"))
    service = _make_service(llm=llm, agent_executor=_FakeAgentExecutor())

    result = await service.simple_chat("问题")

    assert result == Messages.LLM_INVALID_API_KEY("AI")


# ===== stream_chat =====


# 未初始化 LLM 时流式对话下发单条初始化错误帧
@pytest.mark.anyio
async def test_stream_chat_yields_error_frame_without_llm() -> None:
    service = _make_service()
    frames = await _collect_frames(service.stream_chat("问题"))
    assert frames == [{"type": "error", "content": Messages.INITIALIZATION_ERROR}]


# 直连流式对话逐块下发内容并跳过空块
@pytest.mark.anyio
async def test_stream_chat_direct_streams_content_chunks() -> None:
    llm = _FakeStreamingLLM(
        chunks=[_FakeChunk("he"), _FakeChunk("llo"), _FakeChunk("")]
    )
    service = _make_service(llm=llm)

    frames = await _collect_frames(service.stream_chat("问题"))

    assert frames == [
        {"type": "content", "content": "he"},
        {"type": "content", "content": "llo"},
    ]


# 直连流式异常解析为超时文案并以内容帧下发
@pytest.mark.anyio
async def test_stream_chat_direct_stream_error_is_resolved() -> None:
    llm = _FakeStreamingLLM(stream_error=RuntimeError("request timeout"))
    service = _make_service(llm=llm)

    frames = await _collect_frames(service.stream_chat("问题"))

    assert frames == [{"type": "content", "content": Messages.REQUEST_TIMEOUT_ERROR}]


# 权限不足时先下发思考帧再逐字下发无权限内容
@pytest.mark.anyio
async def test_stream_chat_permission_denied_emits_thinking_then_message() -> None:
    router = _FakeIntentRouter(
        permission_result=("log_analysis", False, "无权限", "structured")
    )
    service = _make_service(
        llm=_FakeStreamingLLM(),
        intent_router=router,
        agent_executor=_FakeAgentExecutor(),
    )

    frames = await _collect_frames(
        service.stream_chat("查日志", user_id=5, db=MagicMock())
    )

    assert frames[0] == {
        "type": "thinking",
        "content": Messages.PERMISSION_DENIED_STREAM_THINKING("log_analysis"),
    }
    assert [f["content"] for f in frames[1:]] == ["无", "权", "限"]
    assert all(f["type"] == "content" for f in frames[1:])


# agent 流式对话下发思考步骤与最终结论帧，末尾跟随内容块
@pytest.mark.anyio
async def test_stream_chat_agent_emits_tool_steps_and_final_result() -> None:
    events = [
        {
            "event": "on_tool_start",
            "name": "SpringSqlTool",
            "run_id": "r1",
            "data": {"input": "SELECT 1"},
        },
        {
            "event": "on_tool_end",
            "name": "SpringSqlTool",
            "run_id": "r1",
            "data": {"output": "rows-1"},
        },
        {"event": "on_chain_end", "data": {"output": {"output": "最终答复"}}},
    ]
    router = _FakeIntentRouter(route_result=("log_analysis", "text_fallback"))
    executor = _FakeAgentExecutor(events=events)
    llm = _FakeStreamingLLM(chunks=[_FakeChunk("回顾-"), _FakeChunk("结束")])
    service = _make_service(llm=llm, intent_router=router, agent_executor=executor)

    frames = await _collect_frames(service.stream_chat("查日志"))

    assert frames[0] == {
        "type": "thinking",
        "content": Messages.AGENT_EXECUTION_PROCESS_HEADER(),
    }
    assert frames[1]["content"] == Messages.AGENT_EXECUTION_STEP_START(
        1, "SpringSqlTool", "SELECT 1"
    )
    assert frames[2]["content"] == Messages.AGENT_EXECUTION_STEP_RESULT("rows-1")
    assert {
        "type": "thinking",
        "content": Messages.AGENT_FINAL_RESULT("最终答复"),
    } in frames
    assert frames[-2:] == [
        {"type": "content", "content": "回顾-"},
        {"type": "content", "content": "结束"},
    ]
    payload = executor.astream_events_calls[0]["payload"]
    assert payload["input"] == Messages.CURRENT_QUESTION("查日志")


# agent 最终流内容为空时回退到同步调用结果
@pytest.mark.anyio
async def test_stream_chat_agent_empty_final_stream_falls_back_to_invoke() -> None:
    events = [{"event": "on_chain_end", "data": {"output": {"output": "答复"}}}]
    router = _FakeIntentRouter(route_result=("log_analysis", "text_fallback"))
    executor = _FakeAgentExecutor(events=events)
    llm = _FakeStreamingLLM(chunks=[], invoke_result=_FakeResponse("兜底文本"))
    service = _make_service(llm=llm, intent_router=router, agent_executor=executor)

    frames = await _collect_frames(service.stream_chat("查日志"))

    assert frames[-1] == {"type": "content", "content": "兜底文本"}
    assert len(llm.invoke_calls) == 1


# agent 执行异常解析为服务错误内容帧
@pytest.mark.anyio
async def test_stream_chat_agent_failure_emits_resolved_error() -> None:
    router = _FakeIntentRouter(route_result=("log_analysis", "text_fallback"))
    executor = _FakeAgentExecutor(stream_error=RuntimeError("agent boom"))
    service = _make_service(
        llm=_FakeStreamingLLM(), intent_router=router, agent_executor=executor
    )

    frames = await _collect_frames(service.stream_chat("查日志"))

    assert frames == [
        {"type": "content", "content": Messages.LLM_SERVICE_ERROR("AI", "agent boom")}
    ]


# ===== 工具并行加载 =====


def _success_factory(tools: list[str]) -> tuple[MagicMock, MagicMock]:
    instance = MagicMock()
    instance.get_langchain_tools.return_value = tools
    return MagicMock(return_value=instance), instance


def _failing_factory(message: str = "load failed") -> MagicMock:
    return MagicMock(side_effect=RuntimeError(message))


# 工具分组加载失败互相隔离，成功的工具按声明顺序合并
def test_initialize_ai_tools_isolates_group_failures_and_keeps_order() -> None:
    fastapi_factory, fastapi_instance = _success_factory(["fastapi-1", "fastapi-2"])
    spring_factory = _failing_factory()
    rag_factory, rag_instance = _success_factory(["rag-1"])
    neo4j_factory = _failing_factory()
    mongodb_factory, mongodb_instance = _success_factory(["mongo-1", "mongo-2"])
    warehouse_factory, _ = _success_factory(["wh-1"])

    factories = AgentToolFactories(
        sql_tools=(("FastAPI", fastapi_factory), ("Spring", spring_factory)),
        rag=("RAG", rag_factory),
        neo4j=("Neo4j 知识图谱", neo4j_factory),
        mongodb=("MongoDB 日志", mongodb_factory),
        warehouse=("ClickHouse 数仓", warehouse_factory),
    )

    sql_instance, rag_out, mongodb_out, all_tools = initialize_ai_tools(
        tool_factories=factories
    )

    assert sql_instance is fastapi_instance
    assert rag_out is rag_instance
    assert mongodb_out is mongodb_instance
    assert all_tools == [
        "fastapi-1",
        "fastapi-2",
        "rag-1",
        "mongo-1",
        "mongo-2",
        "wh-1",
    ]


# include_sql 为假时跳过 SQL 工具组且不调用其工厂
def test_initialize_ai_tools_skips_sql_group_when_disabled() -> None:
    fastapi_factory, _ = _success_factory(["fastapi-1"])
    rag_factory, _ = _success_factory(["rag-1"])
    mongodb_factory, _ = _success_factory(["mongo-1"])
    factories = AgentToolFactories(
        sql_tools=(("FastAPI", fastapi_factory),),
        rag=("RAG", rag_factory),
        neo4j=("Neo4j", _failing_factory()),
        mongodb=("MongoDB", mongodb_factory),
        warehouse=("ClickHouse", _failing_factory()),
    )

    sql_instance, _, _, all_tools = initialize_ai_tools(
        include_sql=False, tool_factories=factories
    )

    assert sql_instance is None
    assert fastapi_factory.call_count == 0
    assert "fastapi-1" not in all_tools


# include_logs 为假时跳过日志工具组且不调用其工厂
def test_initialize_ai_tools_skips_mongodb_group_when_logs_disabled() -> None:
    mongodb_factory, _ = _success_factory(["mongo-1"])
    factories = AgentToolFactories(
        sql_tools=(),
        rag=("RAG", _failing_factory()),
        neo4j=("Neo4j", _failing_factory()),
        mongodb=("MongoDB", mongodb_factory),
        warehouse=("ClickHouse", _failing_factory()),
    )

    _, _, mongodb_out, all_tools = initialize_ai_tools(
        include_logs=False, tool_factories=factories
    )

    assert mongodb_out is None
    assert mongodb_factory.call_count == 0
    assert "mongo-1" not in all_tools


# SQL 工具组返回首个成功实例并跳过加载失败的分组
def test_load_sql_tools_returns_first_instance_and_skips_failed_group() -> None:
    good_a, instance_a = _success_factory(["a1"])
    good_b, _ = _success_factory(["b1"])

    instance, tools = base_module._load_sql_tools(
        [("A", good_a), ("B", _failing_factory()), ("C", good_b)]
    )

    assert instance is instance_a
    assert tools == ["a1", "b1"]


# 工具组加载成功返回实例与工具，失败返回空值
def test_load_tool_group_returns_none_and_empty_on_failure() -> None:
    good, instance = _success_factory(["t1"])
    assert base_module._load_tool_group("RAG", good) == (instance, ["t1"])

    failed_instance, failed_tools = base_module._load_tool_group(
        "RAG", _failing_factory()
    )
    assert failed_instance is None
    assert failed_tools == []


# ===== __init__ 配置读取 =====


# 初始化按配置构建 LLM 客户端并回填模型名、密钥与超时
def test_init_builds_llm_client_from_config(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = _patch_llm_stack(
        monkeypatch,
        {
            "api_key": "unit-test-value",
            "base_url": "https://llm.local/v1",
            "model_name": "closeai-default",
            "timeout": "18",
        },
    )

    service = BaseAiService(AsyncMock())

    assert service.model_name == "closeai-default"
    assert service._timeout == 18
    assert service._api_key == "unit-test-value"
    assert service.llm is fake_client.return_value
    kwargs = fake_client.call_args.kwargs
    assert kwargs["model"] == "closeai-default"
    assert kwargs["base_url"] == "https://llm.local/v1"
    assert kwargs["timeout"] == 18
    assert kwargs["temperature"] == 0.7


# 配置缺少 api_key 时初始化重置状态且不创建客户端
def test_init_resets_runtime_state_when_config_incomplete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = _patch_llm_stack(
        monkeypatch,
        {"base_url": "https://llm.local/v1", "model_name": "m"},
    )

    service = BaseAiService(AsyncMock())

    assert service.llm is None
    assert fake_client.call_count == 0


# 配置读取抛错时初始化失败并将 LLM 置空
def test_init_resets_runtime_state_when_config_load_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        base_module, "load_config", MagicMock(side_effect=RuntimeError("config boom"))
    )
    monkeypatch.setattr(base_module, "ChatOpenAI", MagicMock())
    monkeypatch.setattr(
        BaseAiService, "_initialize_agent_stack", lambda self, max_iterations=5: None
    )

    service = BaseAiService(AsyncMock())

    assert service.llm is None


# 指定模型键缺失时回退读取默认的 model_name
def test_init_reads_model_key_with_default_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_llm_stack(
        monkeypatch,
        {
            "api_key": "unit-test-value",
            "base_url": "https://llm.local/v1",
            "model_name": "fallback-model",
        },
    )

    service = BaseAiService(AsyncMock(), model_config_key="gpt_model_name")

    assert service.model_name == "fallback-model"
