"""
缓存模块
"""
from .articleCache import ArticleCache, get_article_cache
from .categoryCache import CategoryCache, get_category_cache
from .publishTimeCache import PublishTimeCache, get_publish_time_cache
from .statisticsCache import StatisticsCache, get_statistics_cache
from .wordcloudCache import WordcloudCache, get_wordcloud_cache

__all__: list[str] = [
    'ArticleCache',
    'get_article_cache',
    'CategoryCache',
    'get_category_cache',
    'PublishTimeCache',
    'get_publish_time_cache',
    'StatisticsCache',
    'get_statistics_cache',
    'WordcloudCache',
    'get_wordcloud_cache',
]
