from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class AdsApiAverageSpeed(WarehouseModel):
    __tablename__ = "ads_api_average_speed"
    api_path = Column(types.String, primary_key=True)
    api_method = Column(types.String, primary_key=True)
    api_description = Column(types.String, primary_key=True)
    avg_response_time = Column(types.Float64)
    call_count = Column(types.Int64)
    stat_time = Column(types.DateTime)
