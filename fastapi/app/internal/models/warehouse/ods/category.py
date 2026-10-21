from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class OdsCategory(WarehouseModel):
    """ClickHouse ODS 层一级分类表 ods_category，存储从 MySQL 同步的分类原始数据"""

    __tablename__ = "ods_category"
    id = Column(types.Int64, primary_key=True)
    name = Column(types.String)
    create_time = Column(types.DateTime)
    update_time = Column(types.DateTime)
