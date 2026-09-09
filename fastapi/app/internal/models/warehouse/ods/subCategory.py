from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class OdsSubCategory(WarehouseModel):
    __tablename__ = "ods_sub_category"
    id = Column(types.Int64, primary_key=True)
    name = Column(types.String)
    category_id = Column(types.Int64)
    create_time = Column(types.DateTime)
    update_time = Column(types.DateTime)
