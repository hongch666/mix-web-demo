from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class OdsCategory(WarehouseModel):
    __tablename__ = "ods_category"
    id = Column(types.Int64, primary_key=True)
    name = Column(types.String)
    create_time = Column(types.DateTime)
    update_time = Column(types.DateTime)
