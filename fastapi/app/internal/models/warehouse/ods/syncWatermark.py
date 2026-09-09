from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class SyncWatermark(WarehouseModel):
    __tablename__ = "sync_watermark"
    table_name = Column(types.String, primary_key=True)
    last_watermark = Column(types.String)
    updated_at = Column(types.DateTime)
