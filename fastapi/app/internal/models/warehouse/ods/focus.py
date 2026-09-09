from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class OdsFocus(WarehouseModel):
    __tablename__ = "ods_focus"
    id = Column(types.Int64, primary_key=True)
    user_id = Column(types.Int64)
    focus_id = Column(types.Int64)
    created_time = Column(types.DateTime)
