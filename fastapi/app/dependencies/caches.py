from typing import Annotated

from fastapi import Depends

from app.internal.cache import (
    ApiLogCalledCountCache,
    ApiLogSpeedCache,
    ArticleCache,
    CategoryCache,
    PublishTimeCache,
    StatisticsCache,
    UserDayCache,
    UserStatsCache,
    UserViewCache,
    WordcloudCache,
    get_api_log_called_count_cache,
    get_api_log_speed_cache,
    get_article_cache,
    get_category_cache,
    get_publish_time_cache,
    get_statistics_cache,
    get_user_day_cache,
    get_user_stats_cache,
    get_user_view_cache,
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


def provide_api_log_speed_cache(logger: LoggerDep) -> ApiLogSpeedCache:
    """装配接口平均响应时间缓存单例，logger 由 FastAPI 依赖注入提供"""
    return get_api_log_speed_cache(logger)


def provide_api_log_called_count_cache(logger: LoggerDep) -> ApiLogCalledCountCache:
    """装配接口调用次数缓存单例，logger 由 FastAPI 依赖注入提供"""
    return get_api_log_called_count_cache(logger)


def provide_user_day_cache(logger: LoggerDep) -> UserDayCache:
    """装配用户日趋势缓存单例，logger 由 FastAPI 依赖注入提供"""
    return get_user_day_cache(logger)


def provide_user_stats_cache(logger: LoggerDep) -> UserStatsCache:
    """装配用户统计总览缓存单例，logger 由 FastAPI 依赖注入提供"""
    return get_user_stats_cache(logger)


def provide_user_view_cache(logger: LoggerDep) -> UserViewCache:
    """装配用户文章阅读分布缓存单例，logger 由 FastAPI 依赖注入提供"""
    return get_user_view_cache(logger)


ArticleCacheDep = Annotated[ArticleCache, Depends(provide_article_cache)]
CategoryCacheDep = Annotated[CategoryCache, Depends(provide_category_cache)]
PublishTimeCacheDep = Annotated[PublishTimeCache, Depends(provide_publish_time_cache)]
StatisticsCacheDep = Annotated[StatisticsCache, Depends(provide_statistics_cache)]
WordcloudCacheDep = Annotated[WordcloudCache, Depends(provide_wordcloud_cache)]
ApiLogSpeedCacheDep = Annotated[ApiLogSpeedCache, Depends(provide_api_log_speed_cache)]
ApiLogCalledCountCacheDep = Annotated[
    ApiLogCalledCountCache, Depends(provide_api_log_called_count_cache)
]
UserDayCacheDep = Annotated[UserDayCache, Depends(provide_user_day_cache)]
UserStatsCacheDep = Annotated[UserStatsCache, Depends(provide_user_stats_cache)]
UserViewCacheDep = Annotated[UserViewCache, Depends(provide_user_view_cache)]
