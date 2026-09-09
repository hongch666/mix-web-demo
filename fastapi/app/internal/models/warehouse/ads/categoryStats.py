from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class AdsCategoryStats(WarehouseModel):
    __tablename__ = "ads_category_stats"
    parent_category_id = Column(types.Int64, primary_key=True)
    category_name = Column(types.String)
    article_count = Column(types.Int64)
    stat_time = Column(types.DateTime)
