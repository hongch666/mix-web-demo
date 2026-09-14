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

ArticleCacheDep = Annotated[ArticleCache, Depends(get_article_cache)]
CategoryCacheDep = Annotated[CategoryCache, Depends(get_category_cache)]
PublishTimeCacheDep = Annotated[PublishTimeCache, Depends(get_publish_time_cache)]
StatisticsCacheDep = Annotated[StatisticsCache, Depends(get_statistics_cache)]
WordcloudCacheDep = Annotated[WordcloudCache, Depends(get_wordcloud_cache)]
