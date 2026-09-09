from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class DwdApiCall(WarehouseModel):
    __tablename__ = "dwd_api_call"
    event_id = Column(types.String, primary_key=True)
    api_path = Column(types.String)
    api_method = Column(types.String)
    api_description = Column(types.String)
    user_id = Column(types.Int64)
    username = Column(types.String)
    response_time = Column(types.Float64)
    action_date = Column(types.Date)
    action_time = Column(types.DateTime)
