from contextlib import nullcontext
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.constants import Messages
from app.internal.schemas import VectorSearchEnhanceReq
from app.internal.services.vectorSearch import vectorSearchService as service_module
from app.internal.services.vectorSearch.vectorSearchService import (
    VectorSearchService,
    get_vector_search_service,
)


class _FakeDoc:
    """仅暴露向量检索结果所需的 page_content 与 metadata 属性"""

    def __init__(self, page_content: str, metadata: dict) -> None:
        self.page_content = page_content
        self.metadata = metadata


@pytest.fixture(autouse=True)
def langsmith_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """替换日志与 LangSmith 上下文，并记录上下文入参"""
    monkeypatch.setattr(service_module, "Logger", Mock())
    captured: list[dict] = []

    def _context(**kwargs):
        captured.append(kwargs)
        return nullcontext()

    monkeypatch.setattr(service_module, "get_langsmith_context", _context)
    return captured


def _make_service(mapper, **overrides) -> VectorSearchService:
    params = {
        "enabled": True,
        "candidate_limit": 10,
        "fetch_multiplier": 2,
        "max_matched_chunks": 2,
        "min_score": 0.3,
        "score_mode": "similarity",
        "vector_mapper": mapper,
    }
    params.update(overrides)
    return VectorSearchService(**params)


# 服务关闭时直接返回空且不查询向量库
@pytest.mark.anyio
async def test_disabled_service_returns_empty_without_query() -> None:
    mapper = AsyncMock()
    service = _make_service(mapper, enabled=False)

    resp = await service.enhance(VectorSearchEnhanceReq(keyword="k", articleIds=[1]))

    assert resp.items == []
    mapper.similarity_search_with_score.assert_not_awaited()


# 关键词为空白时返回空且不查询向量库
@pytest.mark.anyio
async def test_blank_keyword_returns_empty() -> None:
    mapper = AsyncMock()
    service = _make_service(mapper)

    resp = await service.enhance(VectorSearchEnhanceReq(keyword="   ", articleIds=[1]))

    assert resp.items == []
    mapper.similarity_search_with_score.assert_not_awaited()


# articleIds 为空时返回空且不查询向量库
@pytest.mark.anyio
async def test_missing_article_ids_returns_empty() -> None:
    mapper = AsyncMock()
    service = _make_service(mapper)

    resp = await service.enhance(VectorSearchEnhanceReq(keyword="k", articleIds=[]))

    assert resp.items == []
    mapper.similarity_search_with_score.assert_not_awaited()


# articleIds 全为非法值时返回空且不查询向量库
@pytest.mark.anyio
async def test_all_invalid_ids_returns_empty() -> None:
    mapper = AsyncMock()
    service = _make_service(mapper)

    resp = await service.enhance(
        VectorSearchEnhanceReq(keyword="k", articleIds=[0, -3])
    )

    assert resp.items == []
    mapper.similarity_search_with_score.assert_not_awaited()


# 按文章聚合分块、过滤无效与低分行并按分数排序
@pytest.mark.anyio
async def test_enhance_groups_chunks_and_orders_items(langsmith_calls) -> None:
    mapper = AsyncMock()
    mapper.similarity_search_with_score.return_value = [
        (
            _FakeDoc(
                "  content 1 ", {"article_id": 1, "title": "T1", "chunk_index": 0}
            ),
            0.9,
        ),
        (
            _FakeDoc("content 2", {"article_id": 1, "title": "T1", "chunk_index": 1}),
            0.7,
        ),
        (
            _FakeDoc("content 3", {"article_id": 2, "title": "T2", "chunk_index": 0}),
            0.95,
        ),
        (_FakeDoc("ignored", {"article_id": 99, "title": "X", "chunk_index": 0}), 0.99),
        (_FakeDoc("low", {"article_id": 2, "title": "T2", "chunk_index": 1}), 0.1),
    ]
    service = _make_service(mapper)

    resp = await service.enhance(
        VectorSearchEnhanceReq(keyword="搜索", articleIds=[1, 2], topK=5)
    )

    assert [item.articleId for item in resp.items] == [2, 1]
    by_id = {item.articleId: item for item in resp.items}
    assert by_id[2].vectorScore == 0.95
    assert len(by_id[2].matchedChunks) == 1
    assert by_id[1].vectorScore == 0.9
    assert [chunk.score for chunk in by_id[1].matchedChunks] == [0.9, 0.7]
    assert by_id[1].matchedChunks[0].content == "content 1"
    mapper.similarity_search_with_score.assert_awaited_once_with("搜索", 10)
    assert langsmith_calls[0]["name"] == "vector.enhance"
    assert langsmith_calls[0]["metadata"]["candidate_count"] == 2
    assert langsmith_calls[0]["metadata"]["fetch_k"] == 10


# 命中分块按 max_matched_chunks 截断且取最高分
@pytest.mark.anyio
async def test_enhance_truncates_matched_chunks() -> None:
    mapper = AsyncMock()
    mapper.similarity_search_with_score.return_value = [
        (
            _FakeDoc(f"c{i}", {"article_id": 1, "title": "T", "chunk_index": i}),
            0.5 + i * 0.1,
        )
        for i in range(4)
    ]
    service = _make_service(mapper, max_matched_chunks=2, min_score=0.0)

    resp = await service.enhance(
        VectorSearchEnhanceReq(keyword="k", articleIds=[1], topK=4)
    )

    assert len(resp.items[0].matchedChunks) == 2
    assert [chunk.score for chunk in resp.items[0].matchedChunks] == [0.8, 0.7]
    assert resp.items[0].vectorScore == 0.8


# 未注入 mapper 时回退到工厂 mapper 并执行查询
@pytest.mark.anyio
async def test_enhance_falls_back_to_factory_mapper_when_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mapper = AsyncMock()
    mapper.similarity_search_with_score.return_value = []
    monkeypatch.setattr(service_module, "get_vector_store_mapper", lambda: mapper)
    service = _make_service(None)

    resp = await service.enhance(VectorSearchEnhanceReq(keyword="k", articleIds=[1]))

    assert resp.items == []
    mapper.similarity_search_with_score.assert_awaited_once()


# 分数高中低三段分别映射到对应的原因文案
@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.85, Messages.VECTOR_SEARCH_REASON_HIGH),
        (0.65, Messages.VECTOR_SEARCH_REASON_MEDIUM),
        (0.2, Messages.VECTOR_SEARCH_REASON_LOW),
    ],
)
def test_generate_reason_maps_score_bands(score: float, expected: str) -> None:
    assert VectorSearchService()._generate_reason(score) == expected


# similarity 模式分数裁剪到 0 到 1 区间
def test_normalize_score_similarity_clamps_range() -> None:
    service = _make_service(AsyncMock())

    assert service._normalize_score(1.5) == 1.0
    assert service._normalize_score(-0.2) == 0.0
    assert service._normalize_score(0.42) == 0.42


# distance 模式把距离反转为相似度
def test_normalize_score_distance_mode_inverts() -> None:
    service = _make_service(AsyncMock(), score_mode="distance", min_score=0.0)

    assert service._normalize_score(0.0) == 1.0
    assert service._normalize_score(3.0) == pytest.approx(0.25)


# 非法 score_mode 回退为 similarity
def test_invalid_score_mode_falls_back_to_similarity() -> None:
    assert _make_service(AsyncMock(), score_mode="cosine").score_mode == "similarity"


# articleIds 去重、过滤非法值并按候选上限截断
def test_normalize_article_ids_dedupes_filters_and_limits() -> None:
    service = _make_service(AsyncMock(), candidate_limit=3)

    assert service._normalize_article_ids([1, 1, 2, -5, 3, 4], 0) == [1, 2, 3]


# 请求 limit 生效并按候选上限截断 articleIds
def test_normalize_article_ids_honors_request_limit() -> None:
    service = _make_service(AsyncMock(), candidate_limit=5)

    assert service._normalize_article_ids([1, 2, 3, 4], 2) == [1, 2]


# fetch_k 按倍数计算并受候选上限与最小分块数约束
def test_resolve_fetch_k_uses_multiplier_and_floor() -> None:
    service = _make_service(
        AsyncMock(), candidate_limit=10, fetch_multiplier=3, max_matched_chunks=4
    )

    assert service._resolve_fetch_k(2, 2) == 6
    assert service._resolve_fetch_k(0, 1) == 4
    assert service._resolve_fetch_k(1, 8) == 24
    assert service._resolve_fetch_k(50, 3) == 30


# to_int 转换字符串与浮点，非法值返回 None
def test_to_int_handles_invalid_values() -> None:
    service = _make_service(AsyncMock())

    assert service._to_int("5") == 5
    assert service._to_int(2.9) == 2
    assert service._to_int("abc") is None
    assert service._to_int(None) is None


# 查询串包含关键词、分类、子分类与清洗后的标签
def test_build_query_includes_filters_and_tags() -> None:
    service = _make_service(AsyncMock())
    req = VectorSearchEnhanceReq(
        keyword="搜索",
        categoryName="科技",
        subCategoryName="AI",
        tags=["a", "", " b "],
    )

    lines = service._build_query("搜索", req).splitlines()

    assert lines[0] == "搜索"
    assert any("科技" in line for line in lines)
    assert any("AI" in line for line in lines)
    assert any("a, b" in line for line in lines)


# 标签最多拼接 10 个，超出的被忽略
def test_build_query_limits_tags_to_ten() -> None:
    service = _make_service(AsyncMock())
    req = VectorSearchEnhanceReq(keyword="k", tags=[f"t{i}" for i in range(12)])

    query = service._build_query("k", req)

    assert "t9" in query
    assert "t10" not in query


# 内容中的连续空白折叠为单个空格
def test_trim_content_collapses_whitespace() -> None:
    service = _make_service(AsyncMock())

    assert service._trim_content("a   b\n\tc") == "a b c"


# 超长内容截断到 220 字符并追加省略号
def test_trim_content_appends_ellipsis_when_too_long() -> None:
    service = _make_service(AsyncMock())

    trimmed = service._trim_content("x" * 300)

    assert len(trimmed) == 223
    assert trimmed.endswith("...")


# 工厂函数返回同一缓存单例
def test_factory_returns_cached_singleton() -> None:
    assert get_vector_search_service() is get_vector_search_service()
