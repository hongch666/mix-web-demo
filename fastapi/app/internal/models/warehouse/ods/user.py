from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class OdsUser(WarehouseModel):
    """ClickHouse ODS 层用户表 ods_user，存储从 MySQL 同步的用户原始快照"""

    __tablename__ = "ods_user"
    id = Column(types.Int64, primary_key=True)
    name = Column(types.String)
    role = Column(types.String)
    img = Column(types.String)
    signature = Column(types.String)
    create_at = Column(types.DateTime)
    update_at = Column(types.DateTime)
