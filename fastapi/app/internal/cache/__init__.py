from typing import List

from app.core.db import get_redis_client

from .articleCache import ArticleCache, get_article_cache
from .baseCache import BaseCache
from .categoryCache import CategoryCache, get_category_cache
from .publishTimeCache import PublishTimeCache, get_publish_time_cache
from .statisticsCache import StatisticsCache, get_statistics_cache
from .versionedCache import VersionedCache
from .wordcloudCache import WordcloudCache, get_wordcloud_cache

__all__: List[str] = [
    "BaseCache",
    "ArticleCache",
    "get_article_cache",
    "CategoryCache",
    "get_category_cache",
    "PublishTimeCache",
    "get_publish_time_cache",
    "StatisticsCache",
    "get_statistics_cache",
    "VersionedCache",
    "WordcloudCache",
    "get_wordcloud_cache",
    "get_redis_client",
]
