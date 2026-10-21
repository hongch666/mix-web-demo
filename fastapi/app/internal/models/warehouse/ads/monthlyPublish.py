from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class AdsMonthlyPublish(WarehouseModel):
    """ClickHouse ADS 层月度发布统计表 ads_monthly_publish，按年月统计文章发布量"""

    __tablename__ = "ads_monthly_publish"
    year_month = Column(types.String, primary_key=True)
    article_count = Column(types.Int64)
    stat_time = Column(types.DateTime)
