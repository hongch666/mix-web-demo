from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class AdsTop10Article(WarehouseModel):
    """ClickHouse ADS 层热门文章 Top10 表 ads_top10_articles，记录文章标题、标签、浏览量、作者与子分类信息"""

    __tablename__ = "ads_top10_articles"
    id = Column(types.Int64, primary_key=True)
    title = Column(types.String)
    tags = Column(types.String)
    status = Column(types.Int8)
    views = Column(types.Int32)
    create_at = Column(types.DateTime)
    update_at = Column(types.DateTime)
    user_id = Column(types.Int64)
    user_name = Column(types.String)
    sub_category_id = Column(types.Int64)
    stat_time = Column(types.DateTime)
