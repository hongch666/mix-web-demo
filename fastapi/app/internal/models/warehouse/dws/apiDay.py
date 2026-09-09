from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class DwsApiDay(WarehouseModel):
    __tablename__ = "dws_api_day"
    action_date = Column(types.Date, primary_key=True)
    api_path = Column(types.String, primary_key=True)
    api_method = Column(types.String, primary_key=True)
    api_description = Column(types.String, primary_key=True)
    call_count = Column(types.Int64)
    total_response_time = Column(types.Float64)
    max_response_time = Column(types.Float64)
