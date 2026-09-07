import asyncio
from unittest.mock import AsyncMock

from app.internal.services.analyze.analyzeService import AnalyzeService


def test_get_keywords_dic_prefers_ads_keywords() -> None:
    article_mapper: AsyncMock = AsyncMock()
    article_mapper.get_search_keywords_clickhouse_mapper_async.return_value = [
        "FastAPI",
        "NestJS",
    ]
    service: AnalyzeService = AnalyzeService(articleMapper=article_mapper)
    service._nestjs_client.get_search_keywords = AsyncMock(return_value=["fallback"])

    result = asyncio.run(service.get_keywords_dic())

    assert result == {"FastAPI": 1, "NestJS": 1}
    service._nestjs_client.get_search_keywords.assert_not_awaited()


def test_get_keywords_dic_falls_back_to_nestjs_when_ads_query_fails() -> None:
    article_mapper: AsyncMock = AsyncMock()
    article_mapper.get_search_keywords_clickhouse_mapper_async.side_effect = (
        RuntimeError("ClickHouse 不可用")
    )
    service: AnalyzeService = AnalyzeService(articleMapper=article_mapper)
    service._nestjs_client.get_search_keywords = AsyncMock(return_value=["FastAPI"])

    result = asyncio.run(service.get_keywords_dic())

    assert result == {"FastAPI": 1}
    service._nestjs_client.get_search_keywords.assert_awaited_once()


def test_get_keywords_dic_falls_back_to_nestjs_when_ads_is_empty() -> None:
    article_mapper: AsyncMock = AsyncMock()
    article_mapper.get_search_keywords_clickhouse_mapper_async.return_value = []
    service: AnalyzeService = AnalyzeService(articleMapper=article_mapper)
    service._nestjs_client.get_search_keywords = AsyncMock(return_value=["FastAPI"])

    result = asyncio.run(service.get_keywords_dic())

    assert result == {"FastAPI": 1}
    service._nestjs_client.get_search_keywords.assert_awaited_once()
