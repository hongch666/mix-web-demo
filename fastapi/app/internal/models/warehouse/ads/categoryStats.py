from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class AdsCategoryStats(WarehouseModel):
    """ClickHouse ADS 层分类文章统计表 ads_category_stats，记录各父分类下的文章数量"""

    __tablename__ = "ads_category_stats"
    parent_category_id = Column(types.Int64, primary_key=True)
    category_name = Column(types.String)
    article_count = Column(types.Int64)
    stat_time = Column(types.DateTime)
