from functools import lru_cache
from common.client import call_remote_service

from entity.po import Article

class ArticleMapper:

    async def get_all_articles_mapper(self) -> list[Article]:
        # 使用Spring部分获取日志数据
        result = await call_remote_service(
            service_name="spring",
            path="/articles/list",
            method="GET"
        )
        return result["data"]["list"]
    
@lru_cache()
def get_article_mapper() -> ArticleMapper:
    return ArticleMapper()