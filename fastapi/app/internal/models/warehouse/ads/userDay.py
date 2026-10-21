from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class AdsUserDay(WarehouseModel):
    """ClickHouse ADS 层用户日活跃表 ads_user_day，按日统计用户点赞、收藏、评论、关注与浏览量"""

    __tablename__ = "ads_user_day"
    stat_date = Column(types.Date, primary_key=True)
    user_id = Column(types.Int64, primary_key=True)
    like_count = Column(types.Int64)
    collect_count = Column(types.Int64)
    comment_count = Column(types.Int64)
    focus_count = Column(types.Int64)
    view_count = Column(types.Int64)
    last_active_time = Column(types.DateTime)
    stat_time = Column(types.DateTime)
