from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class SyncWatermark(WarehouseModel):
    """ClickHouse 水位表 sync_watermark，记录各源表上次同步到的水位值与更新时间"""

    __tablename__ = "sync_watermark"
    table_name = Column(types.String, primary_key=True)
    last_watermark = Column(types.String)
    updated_at = Column(types.DateTime)
