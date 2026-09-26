"""RAGTools 检索语义（去重、过滤、HyDE、降级）的单元测试"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from langchain_core.documents import Document

from app.core.constants import Messages
from app.internal.agents.tools import ragTools as rag_module
from app.internal.agents.tools.ragTools import RAGTools

AGENT_CONFIG = {
    "embedding": {
        "top_k": 4,
        "similarity_threshold": 0.6,
        "similarity_tolerance": 0.05,
    },
    "closeai": {},
}


class _FakeVectorMapper:
    """替换真实 VectorMapper，仅保留检索侧用到的静态脱敏方法"""

    @staticmethod
    def sanitize_content(content: str) -> str:
        return content


class _FakeMapper:
    def __init__(self) -> None:
        self.similarity_search_with_score = AsyncMock(return_value=[])
        self.as_retriever = Mock(return_value="retriever")


def _build_tools(
    monkeypatch: pytest.MonkeyPatch,
    mapper: _FakeMapper | None = None,
    config: dict | None = None,
) -> tuple[RAGTools, _FakeMapper]:
    monkeypatch.setattr(
        rag_module,
        "load_config",
        lambda section: config if config is not None else AGENT_CONFIG,
    )
    monkeypatch.setattr(rag_module, "set_llm_cache", Mock())
    monkeypatch.setattr(rag_module, "VectorMapper", _FakeVectorMapper)
    resolved_mapper = mapper if mapper is not None else _FakeMapper()
    return RAGTools(resolved_mapper), resolved_mapper


def _doc(article_id: int, content: str) -> Document:
    return Document(page_content=content, metadata={"article_id": article_id})


# 初始化从配置读取 top_k、阈值、容差且无 HyDE 客户端
def test_init_reads_retrieval_parameters_from_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools, _ = _build_tools(monkeypatch)

    assert tools.enabled is True
    assert tools.top_k == 4
    assert tools.similarity_threshold == 0.6
    assert tools.similarity_tolerance == 0.05
    assert tools.hyde_llm is None


# HyDE 客户端构造失败时隔离异常并保持为 None
def test_init_isolates_hyde_client_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _RaisingChatOpenAI:
        def __init__(self, **kwargs):
            raise RuntimeError("model init failed")

    config = {
        "embedding": {
            "top_k": 3,
            "similarity_threshold": 0.5,
            "similarity_tolerance": 0.1,
        },
        "closeai": {"api_key": "unit-test-key", "base_url": "http://llm"},
    }
    monkeypatch.setattr(rag_module, "ChatOpenAI", _RaisingChatOpenAI)

    tools, _ = _build_tools(monkeypatch, config=config)

    assert tools.hyde_llm is None


# 空输入去重返回空列表
def test_deduplicate_returns_empty_for_empty_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools, _ = _build_tools(monkeypatch)

    assert tools._deduplicate_articles([], 3) == []


# 容差内同一文章分块去重后保留不同文章
def test_deduplicate_prefers_distinct_articles_within_tolerance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools, _ = _build_tools(monkeypatch)
    tools.similarity_tolerance = 0.1
    docs = [(_doc(1, "a"), 0.9), (_doc(1, "b"), 0.89), (_doc(2, "c"), 0.88)]

    result = tools._deduplicate_articles(docs, 2)

    assert [doc.metadata["article_id"] for doc, _ in result] == [1, 2]


# 达到 k 后去重停止并保留最高分文章
def test_deduplicate_stops_at_k(monkeypatch: pytest.MonkeyPatch) -> None:
    tools, _ = _build_tools(monkeypatch)
    tools.similarity_tolerance = 0.01
    docs = [(_doc(1, "a"), 0.9), (_doc(2, "b"), 0.85), (_doc(3, "c"), 0.8)]

    result = tools._deduplicate_articles(docs, 1)

    assert len(result) == 1
    assert result[0][0].metadata["article_id"] == 1


# 分差超过容差时同一文章分块被保留
def test_deduplicate_adds_chunks_with_large_score_gap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools, _ = _build_tools(monkeypatch)
    tools.similarity_tolerance = 0.1
    docs = [(_doc(1, "a"), 0.9), (_doc(1, "b"), 0.5)]

    result = tools._deduplicate_articles(docs, 5)

    assert len(result) == 2


# 槽位不足时用同一文章剩余分块补齐
def test_deduplicate_fills_remaining_slots_with_same_article_chunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools, _ = _build_tools(monkeypatch)
    tools.similarity_tolerance = 0.5
    docs = [(_doc(1, "a"), 0.9), (_doc(1, "b"), 0.89)]

    result = tools._deduplicate_articles(docs, 2)

    assert len(result) == 2
    assert {doc.metadata["article_id"] for doc, _ in result} == {1}


# 工具禁用时搜索返回自定义不可用原因且不检索
@pytest.mark.anyio
async def test_search_returns_disabled_message_when_tools_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools, mapper = _build_tools(monkeypatch)
    tools.enabled = False
    tools._init_error_message = "自定义不可用原因"

    assert await tools.search_similar_articles("问题") == "自定义不可用原因"
    mapper.similarity_search_with_score.assert_not_awaited()


# 检索分数低于阈值时返回无相关文章消息
@pytest.mark.anyio
async def test_search_returns_no_relevant_message_when_below_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mapper = _FakeMapper()
    mapper.similarity_search_with_score.return_value = [(_doc(1, "低分内容"), 0.1)]
    tools, _ = _build_tools(monkeypatch, mapper)

    assert (
        await tools.search_similar_articles("问题")
        == Messages.NO_RELEVANT_ARTICLES_FOUND_MESSAGE
    )


# 检索按配置 top_k 放大候选并返回带分数的片段
@pytest.mark.anyio
async def test_search_uses_configured_top_k_and_returns_fragments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mapper = _FakeMapper()
    mapper.similarity_search_with_score.return_value = [(_doc(1, "内容概念"), 0.9)]
    tools, _ = _build_tools(monkeypatch, mapper)

    result = await tools.search_similar_articles("问题")

    args = mapper.similarity_search_with_score.await_args.args
    assert args == ("问题", 30, None)
    assert Messages.RAG_SEARCH_RESULT_HEADER(1, 0.6) in result
    assert "内容概念" in result


# tags 与 user_id 过滤合并为 $and 组合条件
@pytest.mark.anyio
async def test_search_builds_combined_pgvector_filter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mapper = _FakeMapper()
    mapper.similarity_search_with_score.return_value = [(_doc(1, "内容"), 0.9)]
    tools, _ = _build_tools(monkeypatch, mapper)

    await tools.search_similar_articles(
        "问题", tags_filter=["python"], user_id_filter=7
    )

    assert mapper.similarity_search_with_score.await_args.args[2] == {
        "$and": [{"tags": {"$in": ["python"]}}, {"user_id": 7}]
    }


# 仅 tags 过滤时生成单层 pgvector 条件
@pytest.mark.anyio
async def test_search_builds_single_pgvector_filter_for_tags_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mapper = _FakeMapper()
    mapper.similarity_search_with_score.return_value = [(_doc(1, "内容"), 0.9)]
    tools, _ = _build_tools(monkeypatch, mapper)

    await tools.search_similar_articles("问题", tags_filter=["python"])

    assert mapper.similarity_search_with_score.await_args.args[2] == {
        "tags": {"$in": ["python"]}
    }


# 启用 HyDE 时用生成的假设文档替换原查询
@pytest.mark.anyio
async def test_search_replaces_query_with_hyde_document(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mapper = _FakeMapper()
    mapper.similarity_search_with_score.return_value = [(_doc(1, "内容"), 0.9)]
    tools, _ = _build_tools(monkeypatch, mapper)
    tools.hyde_llm = SimpleNamespace(
        ainvoke=AsyncMock(return_value=SimpleNamespace(content="假设文档"))
    )

    await tools.search_similar_articles("原始问题")

    assert mapper.similarity_search_with_score.await_args.args[0] == "假设文档"


# HyDE 失败时回退使用原始查询
@pytest.mark.anyio
async def test_search_falls_back_to_original_query_when_hyde_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mapper = _FakeMapper()
    mapper.similarity_search_with_score.return_value = [(_doc(1, "内容"), 0.9)]
    tools, _ = _build_tools(monkeypatch, mapper)
    tools.hyde_llm = SimpleNamespace(
        ainvoke=AsyncMock(side_effect=RuntimeError("hyde down"))
    )

    await tools.search_similar_articles("原始问题")

    assert mapper.similarity_search_with_score.await_args.args[0] == "原始问题"


# 出现 InvalidApiKey 时禁用工具并返回配置不完整消息
@pytest.mark.anyio
async def test_search_disables_tools_on_invalid_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mapper = _FakeMapper()
    mapper.similarity_search_with_score.side_effect = RuntimeError(
        "InvalidApiKey provided"
    )
    tools, _ = _build_tools(monkeypatch, mapper)

    result = await tools.search_similar_articles("问题")

    assert result == Messages.EMBEDDING_CONFIG_INCOMPLETE_MESSAGE
    assert tools.enabled is False


# 文章上下文按去重后返回 Document 列表
@pytest.mark.anyio
async def test_get_article_context_returns_deduplicated_documents(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mapper = _FakeMapper()
    mapper.similarity_search_with_score.return_value = [
        (_doc(1, "a"), 0.9),
        (_doc(1, "b"), 0.89),
        (_doc(2, "c"), 0.88),
    ]
    tools, _ = _build_tools(monkeypatch, mapper)

    result = await tools.get_article_context("问题", k=2)

    assert len(result) == 2
    assert all(isinstance(doc, Document) for doc in result)


# 工具禁用时文章上下文返回空列表且不检索
@pytest.mark.anyio
async def test_get_article_context_returns_empty_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools, mapper = _build_tools(monkeypatch)
    tools.enabled = False

    assert await tools.get_article_context("问题") == []
    mapper.similarity_search_with_score.assert_not_awaited()


# 检索异常时文章上下文降级返回空列表
@pytest.mark.anyio
async def test_get_article_context_returns_empty_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mapper = _FakeMapper()
    mapper.similarity_search_with_score.side_effect = RuntimeError("vector down")
    tools, _ = _build_tools(monkeypatch, mapper)

    assert await tools.get_article_context("问题") == []


# retriever 使用配置的 top_k 构造
@pytest.mark.anyio
async def test_get_retriever_defaults_to_configured_top_k(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools, mapper = _build_tools(monkeypatch)

    assert await tools.get_retriever() == "retriever"
    mapper.as_retriever.assert_called_once_with(4)


# 暴露的 LangChain 工具名为 RAG 搜索工具
def test_get_langchain_tools_exposes_search_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools, _ = _build_tools(monkeypatch)

    tools_list = tools.get_langchain_tools()

    assert [tool.name for tool in tools_list] == [Messages.RAG_TOOL_NAME]


# get_rag_tools 工厂清缓存前后返回同一实例
def test_get_rag_tools_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rag_module, "load_config", lambda section: AGENT_CONFIG)
    monkeypatch.setattr(rag_module, "set_llm_cache", Mock())
    mapper = _FakeMapper()
    rag_module.get_rag_tools.cache_clear()
    try:
        first = rag_module.get_rag_tools(mapper)
        second = rag_module.get_rag_tools(mapper)
    finally:
        rag_module.get_rag_tools.cache_clear()

    assert first is second
