from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class AdsApiCalledCount(WarehouseModel):
    __tablename__ = "ads_api_called_count"
    api_path = Column(types.String, primary_key=True)
    api_method = Column(types.String, primary_key=True)
    api_description = Column(types.String, primary_key=True)
    call_count = Column(types.Int64)
    avg_response_time = Column(types.Float64)
    stat_time = Column(types.DateTime)
