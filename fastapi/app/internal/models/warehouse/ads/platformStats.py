from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class AdsPlatformStats(WarehouseModel):
    """ClickHouse ADS 层平台整体指标表 ads_platform_stats，汇总浏览、文章、活跃作者、点赞、收藏等总量与均值"""

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
