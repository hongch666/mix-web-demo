from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class OdsFocus(WarehouseModel):
    """ClickHouse ODS 层关注表 ods_focus，存储从 MySQL 同步的用户关注关系原始记录"""

    __tablename__ = "ods_focus"
    id = Column(types.Int64, primary_key=True)
    user_id = Column(types.Int64)
    focus_id = Column(types.Int64)
    created_time = Column(types.DateTime)
