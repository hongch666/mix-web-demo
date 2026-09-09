from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class AdsMonthlyPublish(WarehouseModel):
    __tablename__ = "ads_monthly_publish"
    year_month = Column(types.String, primary_key=True)
    article_count = Column(types.Int64)
    stat_time = Column(types.DateTime)
