from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class AdsPlatformStats(WarehouseModel):
    __tablename__ = "ads_platform_stats"
    id = Column(types.UInt8, primary_key=True)
    stat_time = Column(types.DateTime)
    total_views = Column(types.Int64)
    total_articles = Column(types.Int64)
    active_authors = Column(types.UInt64)
    average_views = Column(types.Float64)
    total_likes = Column(types.Int64)
    average_likes = Column(types.Float64)
    total_collects = Column(types.Int64)
    average_collects = Column(types.Float64)
