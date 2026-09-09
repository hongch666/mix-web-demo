from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class OdsApiLog(WarehouseModel):
    __tablename__ = "ods_api_log"
    event_id = Column(types.String, primary_key=True)
    user_id = Column(types.Int64)
    username = Column(types.String)
    api_description = Column(types.String)
    api_path = Column(types.String)
    api_method = Column(types.String)
    response_time = Column(types.Float64)
    created_at = Column(types.DateTime)
