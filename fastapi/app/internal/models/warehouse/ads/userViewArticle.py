from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class AdsUserViewArticle(WarehouseModel):
    """ClickHouse ADS 层用户浏览文章表 ads_user_view_articles，记录用户对每篇文章的浏览次数"""

    __tablename__ = "ads_user_view_articles"
    user_id = Column(types.Int64, primary_key=True)
    article_id = Column(types.Int64, primary_key=True)
    article_title = Column(types.String)
    view_count = Column(types.Int64)
    stat_time = Column(types.DateTime)
