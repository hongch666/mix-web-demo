from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class AdsUserStats(WarehouseModel):
    """ClickHouse ADS 层用户累计指标表 ads_user_stats，汇总用户主动行为量及被浏览、被点赞、被收藏、粉丝数等被动指标"""

    __tablename__ = "ads_user_stats"
    user_id = Column(types.Int64, primary_key=True)
    total_likes_given = Column(types.Int64)
    total_collects_given = Column(types.Int64)
    total_comments = Column(types.Int64)
    total_focus = Column(types.Int64)
    total_views_given = Column(types.Int64)
    total_articles = Column(types.Int64)
    total_views_received = Column(types.Int64)
    total_likes_received = Column(types.Int64)
    total_collects_received = Column(types.Int64)
    total_followers = Column(types.Int64)
    last_active_time = Column(types.DateTime)
    stat_time = Column(types.DateTime)
