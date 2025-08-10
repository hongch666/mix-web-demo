from sqlmodel import Session, select

from common.client import call_remote_service
from entity.po import Article


# TODO: 使用hadoop全家桶进行计算
async def get_top10_articles_mapper() -> list[dict]:
    articles = await get_all_articles_mapper()
    # 按views降序取前10
    top10 = sorted(articles, key=lambda x: x.get("views", 0), reverse=True)[:10]
    return top10

async def get_all_articles_mapper() -> list[Article]:
    # 使用Spring部分获取日志数据
    result = await call_remote_service(
        service_name="spring",
        path="/articles/list",
        method="GET"
    )
    return result["data"]["list"]