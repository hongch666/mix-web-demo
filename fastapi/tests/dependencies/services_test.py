from app.core.base import LoggerProtocol
from app.dependencies import resolve_analyze_service, resolve_article_mapper
from app.dependencies.caches import (
    provide_article_cache,
    provide_category_cache,
    provide_publish_time_cache,
    provide_statistics_cache,
    provide_wordcloud_cache,
)
from app.dependencies.logger import provide_logger
from app.dependencies.services import provide_analyze_service
from app.internal.clients import get_nestjs_client, get_spring_client


def test_resolve_analyze_service_reuses_request_singleton() -> None:
    """非请求链路与请求链路解析出同一个 AnalyzeService 实例"""
    logger: LoggerProtocol = provide_logger()
    resolved = resolve_analyze_service()
    provided = provide_analyze_service(
        resolve_article_mapper(),
        provide_article_cache(logger),
        provide_category_cache(logger),
        provide_publish_time_cache(logger),
        provide_statistics_cache(logger),
        provide_wordcloud_cache(logger),
        get_spring_client(),
        get_nestjs_client(),
        logger,
    )

    assert resolved is provided
