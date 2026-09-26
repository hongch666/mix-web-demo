from unittest.mock import Mock

import pytest

from app.core.constants import Messages
from app.internal.schemas import GraphRelationDTO, GraphSearchEnhanceReq
from app.internal.services.graphSearch import graphSearchService as service_module
from app.internal.services.graphSearch.graphSearchService import (
    GraphSearchService,
    get_graph_search_service,
)


class _FakeNeo4jClient:
    """记录 Cypher 调用并按脚本返回预设结果的 Fake Neo4j 客户端"""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []
        self.responses: dict[str, object] = {}

    async def run_query(self, cypher: str, params: dict | None = None) -> object:
        self.calls.append((cypher, params or {}))
        response = self.responses.get(cypher)
        if response is None:
            return []
        if isinstance(response, Exception):
            raise response
        return response


class _ExplodingRows:
    """迭代即抛出，用于模拟信号协程在读取结果时失败"""

    def __iter__(self):
        raise RuntimeError("row iteration failed")


@pytest.fixture(autouse=True)
def _silence_logger(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(service_module, "Logger", Mock())


@pytest.fixture
def neo4j_client(monkeypatch: pytest.MonkeyPatch) -> _FakeNeo4jClient:
    client = _FakeNeo4jClient()
    monkeypatch.setattr(service_module, "get_neo4j_client", lambda: client)
    return client


# articleIds 为空时直接返回空结果且不发起任何查询
@pytest.mark.anyio
async def test_empty_article_ids_skips_all_queries(neo4j_client) -> None:
    resp = await GraphSearchService().enhance(GraphSearchEnhanceReq(articleIds=[]))

    assert resp.items == []
    assert neo4j_client.calls == []


# 匿名请求只跑候选相似度，个性化信号分数为 0
@pytest.mark.anyio
async def test_anonymous_request_skips_personal_signals(neo4j_client) -> None:
    resp = await GraphSearchService().enhance(
        GraphSearchEnhanceReq(userId=None, keyword="", articleIds=[1, 2])
    )

    executed = [cypher for cypher, _ in neo4j_client.calls]
    assert executed == [service_module.Scripts.GRAPH_SEARCH_CANDIDATE_SIMILARITY_CYPHER]
    assert [item.articleId for item in resp.items] == [1, 2]
    assert all(item.graphScore == 0.0 for item in resp.items)


# 登录请求执行全部 5 条信号查询并按权重计算图谱分
@pytest.mark.anyio
async def test_authenticated_request_runs_all_signals(neo4j_client) -> None:
    scripts = service_module.Scripts
    neo4j_client.responses[scripts.GRAPH_SEARCH_TAG_INTEREST_CYPHER] = [
        {"articleId": 1, "rawScore": 5, "matchedTags": ["tag-a"]}
    ]
    neo4j_client.responses[scripts.GRAPH_SEARCH_FOLLOWED_AUTHOR_CYPHER] = [
        {"articleId": 1, "names": ["alice"]}
    ]
    neo4j_client.responses[scripts.GRAPH_SEARCH_SAME_SUB_CATEGORY_CYPHER] = [
        {"articleId": 1, "rawScore": 3, "names": ["cat-1"]}
    ]
    neo4j_client.responses[scripts.GRAPH_SEARCH_CANDIDATE_SIMILARITY_CYPHER] = [
        {"articleId": 2, "rawScore": 3, "names": ["shared"]}
    ]
    neo4j_client.responses[scripts.GRAPH_SEARCH_KEYWORD_TAG_CYPHER] = [
        {"articleId": 2, "rawScore": 2, "names": ["keyword-tag"]}
    ]

    resp = await GraphSearchService().enhance(
        GraphSearchEnhanceReq(userId=7, keyword="keyword", articleIds=[1, 2])
    )

    assert len(neo4j_client.calls) == 5
    by_id = {item.articleId: item for item in resp.items}
    assert by_id[1].graphScore == pytest.approx(0.72, abs=1e-4)
    assert {rel.type for rel in by_id[1].relations} == {
        "tag_interest",
        "followed_author",
        "same_sub_category",
    }
    assert by_id[2].graphScore == pytest.approx(0.4, abs=1e-4)
    assert [item.articleId for item in resp.items] == [1, 2]

    tag_params = next(
        params
        for cypher, params in neo4j_client.calls
        if cypher == scripts.GRAPH_SEARCH_TAG_INTEREST_CYPHER
    )
    assert tag_params == {"userId": 7, "articleIds": [1, 2]}


# 各信号叠加后图谱分上限封顶为 1
@pytest.mark.anyio
async def test_graph_score_is_capped_at_one(neo4j_client) -> None:
    scripts = service_module.Scripts
    neo4j_client.responses[scripts.GRAPH_SEARCH_TAG_INTEREST_CYPHER] = [
        {"articleId": 1, "rawScore": 5, "matchedTags": ["t"]}
    ]
    neo4j_client.responses[scripts.GRAPH_SEARCH_FOLLOWED_AUTHOR_CYPHER] = [
        {"articleId": 1, "names": ["a"]}
    ]
    neo4j_client.responses[scripts.GRAPH_SEARCH_SAME_SUB_CATEGORY_CYPHER] = [
        {"articleId": 1, "rawScore": 5, "names": ["c"]}
    ]
    neo4j_client.responses[scripts.GRAPH_SEARCH_CANDIDATE_SIMILARITY_CYPHER] = [
        {"articleId": 1, "rawScore": 3, "names": ["s"]}
    ]
    neo4j_client.responses[scripts.GRAPH_SEARCH_KEYWORD_TAG_CYPHER] = [
        {"articleId": 1, "rawScore": 2, "names": ["k"]}
    ]

    resp = await GraphSearchService().enhance(
        GraphSearchEnhanceReq(userId=1, keyword="k", articleIds=[1])
    )

    assert resp.items[0].graphScore == 1.0


# 单条信号查询失败不影响其他信号计分
@pytest.mark.anyio
async def test_failing_signal_does_not_break_other_signals(neo4j_client) -> None:
    scripts = service_module.Scripts
    neo4j_client.responses[scripts.GRAPH_SEARCH_TAG_INTEREST_CYPHER] = _ExplodingRows()
    neo4j_client.responses[scripts.GRAPH_SEARCH_CANDIDATE_SIMILARITY_CYPHER] = [
        {"articleId": 2, "rawScore": 3, "names": ["shared"]}
    ]

    resp = await GraphSearchService().enhance(
        GraphSearchEnhanceReq(userId=7, keyword="", articleIds=[1, 2])
    )

    by_id = {item.articleId: item for item in resp.items}
    assert by_id[1].graphScore == 0.0
    assert by_id[2].graphScore == pytest.approx(0.2, abs=1e-4)


# Neo4j 查询抛错时吞掉异常，分数与关系为空
@pytest.mark.anyio
async def test_safe_query_swallows_neo4j_error(neo4j_client) -> None:
    scripts = service_module.Scripts
    neo4j_client.responses[scripts.GRAPH_SEARCH_CANDIDATE_SIMILARITY_CYPHER] = (
        RuntimeError("neo4j down")
    )

    resp = await GraphSearchService().enhance(
        GraphSearchEnhanceReq(userId=None, keyword="", articleIds=[1])
    )

    assert resp.items[0].graphScore == 0.0
    assert resp.items[0].relations == []


# 候选上限截断请求的 articleIds 并传入查询参数
@pytest.mark.anyio
async def test_candidate_limit_truncates_requested_ids(neo4j_client) -> None:
    scripts = service_module.Scripts

    resp = await GraphSearchService(candidate_limit=2).enhance(
        GraphSearchEnhanceReq(userId=None, keyword="", articleIds=[1, 2, 3, 4])
    )

    assert [item.articleId for item in resp.items] == [1, 2]
    params = next(
        params
        for cypher, params in neo4j_client.calls
        if cypher == scripts.GRAPH_SEARCH_CANDIDATE_SIMILARITY_CYPHER
    )
    assert params == {"articleIds": [1, 2]}


# 请求 limit 优先于服务候选上限截断结果
@pytest.mark.anyio
async def test_request_limit_overrides_candidate_limit(neo4j_client) -> None:
    resp = await GraphSearchService(candidate_limit=5).enhance(
        GraphSearchEnhanceReq(userId=None, keyword="", articleIds=[1, 2, 3, 4], limit=2)
    )

    assert [item.articleId for item in resp.items] == [1, 2]


# 超长关键词截断为 100 字符后进入查询参数
@pytest.mark.anyio
async def test_keyword_is_truncated_to_100_chars(neo4j_client) -> None:
    scripts = service_module.Scripts

    await GraphSearchService().enhance(
        GraphSearchEnhanceReq(userId=None, keyword="x" * 150, articleIds=[1])
    )

    params = next(
        params
        for cypher, params in neo4j_client.calls
        if cypher == scripts.GRAPH_SEARCH_KEYWORD_TAG_CYPHER
    )
    assert params["keyword"] == "x" * 100


# 缺少 articleId 的行被忽略，不计入图谱分
@pytest.mark.anyio
async def test_rows_without_article_id_are_ignored(neo4j_client) -> None:
    scripts = service_module.Scripts
    neo4j_client.responses[scripts.GRAPH_SEARCH_CANDIDATE_SIMILARITY_CYPHER] = [
        {"rawScore": 3, "names": ["x"]}
    ]

    resp = await GraphSearchService().enhance(
        GraphSearchEnhanceReq(userId=None, keyword="", articleIds=[1])
    )

    assert resp.items[0].graphScore == 0.0


# 多种关系并存时按优先级选择关注作者的文案
def test_generate_reason_prefers_highest_priority_relation() -> None:
    service = GraphSearchService()
    relations = [
        GraphRelationDTO(type="candidate_similarity", name="s", score=0.1, reason="r"),
        GraphRelationDTO(type="tag_interest", name="兴趣", score=0.35, reason="r"),
        GraphRelationDTO(type="followed_author", name="作者", score=0.25, reason="r"),
    ]

    assert service._generate_reason(relations) == "来自你关注的作者 作者"


# 命中小类与标签兴趣时使用标签兴趣文案
def test_generate_reason_uses_interest_template() -> None:
    service = GraphSearchService()
    relations = [
        GraphRelationDTO(type="same_sub_category", name="c", score=0.2, reason="r"),
        GraphRelationDTO(type="tag_interest", name="科技", score=0.35, reason="r"),
    ]

    assert service._generate_reason(relations) == "与你最近点赞/收藏过的标签 科技 相似"


# 仅候选相似度时回退到候选原因常量
def test_generate_reason_falls_back_to_candidate() -> None:
    relations = [
        GraphRelationDTO(type="candidate_similarity", name="s", score=0.2, reason="r")
    ]

    assert (
        GraphSearchService()._generate_reason(relations)
        == Messages.GRAPH_SEARCH_REASON_CANDIDATE
    )


# 无关系时生成的原因文案为空字符串
def test_generate_reason_returns_empty_without_relations() -> None:
    assert GraphSearchService()._generate_reason([]) == ""


# 工厂函数返回同一缓存单例
def test_factory_returns_cached_singleton() -> None:
    assert get_graph_search_service() is get_graph_search_service()
