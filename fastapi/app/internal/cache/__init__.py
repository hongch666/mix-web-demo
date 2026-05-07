from typing import List

from app.core.db import get_redis_client

from .baseCache import BaseCache
from .extend.articleCache import ArticleCache, get_article_cache
from .extend.categoryCache import CategoryCache, get_category_cache
from .extend.publishTimeCache import PublishTimeCache, get_publish_time_cache
from .extend.statisticsCache import StatisticsCache, get_statistics_cache
from .extend.wordcloudCache import WordcloudCache, get_wordcloud_cache
from .versionedCache import VersionedCache

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
