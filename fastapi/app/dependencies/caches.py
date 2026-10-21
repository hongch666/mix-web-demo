from typing import Annotated

from fastapi import Depends

from app.internal.cache import (
    ArticleCache,
    CategoryCache,
    PublishTimeCache,
    StatisticsCache,
    WordcloudCache,
    get_article_cache,
    get_category_cache,
    get_publish_time_cache,
    get_statistics_cache,
    get_wordcloud_cache,
)

from .logger import LoggerDep


def provide_article_cache(logger: LoggerDep) -> ArticleCache:
    """装配文章缓存单例，logger 由 FastAPI 依赖注入提供"""
    return get_article_cache(logger)


def provide_category_cache(logger: LoggerDep) -> CategoryCache:
    """装配分类缓存单例，logger 由 FastAPI 依赖注入提供"""
    return get_category_cache(logger)


def provide_publish_time_cache(logger: LoggerDep) -> PublishTimeCache:
    """装配文章发布时间缓存单例，logger 由 FastAPI 依赖注入提供"""
    return get_publish_time_cache(logger)


def provide_statistics_cache(logger: LoggerDep) -> StatisticsCache:
    """装配平台统计缓存单例，logger 由 FastAPI 依赖注入提供"""
    return get_statistics_cache(logger)


def provide_wordcloud_cache(logger: LoggerDep) -> WordcloudCache:
    """装配词云缓存单例，logger 由 FastAPI 依赖注入提供"""
    return get_wordcloud_cache(logger)


ArticleCacheDep = Annotated[ArticleCache, Depends(provide_article_cache)]
CategoryCacheDep = Annotated[CategoryCache, Depends(provide_category_cache)]
PublishTimeCacheDep = Annotated[PublishTimeCache, Depends(provide_publish_time_cache)]
StatisticsCacheDep = Annotated[StatisticsCache, Depends(provide_statistics_cache)]
WordcloudCacheDep = Annotated[WordcloudCache, Depends(provide_wordcloud_cache)]
