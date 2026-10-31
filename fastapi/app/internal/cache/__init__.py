from app.core.db import get_redis_client

from .baseCache import BaseCache
from .extend.apiLogCalledCountCache import (
    ApiLogCalledCountCache,
    get_api_log_called_count_cache,
)
from .extend.apiLogSpeedCache import ApiLogSpeedCache, get_api_log_speed_cache
from .extend.articleCache import ArticleCache, get_article_cache
from .extend.categoryCache import CategoryCache, get_category_cache
from .extend.publishTimeCache import PublishTimeCache, get_publish_time_cache
from .extend.statisticsCache import StatisticsCache, get_statistics_cache
from .extend.userDayCache import UserDayCache, get_user_day_cache
from .extend.userStatsCache import UserStatsCache, get_user_stats_cache
from .extend.userViewCache import UserViewCache, get_user_view_cache
from .extend.wordcloudCache import WordcloudCache, get_wordcloud_cache
from .keyedVersionedCache import KeyedVersionedCache
from .versionedCache import VersionedCache

__all__: list[str] = [
    "BaseCache",
    "ApiLogCalledCountCache",
    "get_api_log_called_count_cache",
    "ApiLogSpeedCache",
    "get_api_log_speed_cache",
    "ArticleCache",
    "get_article_cache",
    "CategoryCache",
    "get_category_cache",
    "KeyedVersionedCache",
    "PublishTimeCache",
    "get_publish_time_cache",
    "StatisticsCache",
    "get_statistics_cache",
    "UserDayCache",
    "get_user_day_cache",
    "UserStatsCache",
    "get_user_stats_cache",
    "UserViewCache",
    "get_user_view_cache",
    "VersionedCache",
    "WordcloudCache",
    "get_wordcloud_cache",
    "get_redis_client",
]
