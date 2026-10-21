from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class OdsSubCategory(WarehouseModel):
    """ClickHouse ODS 层子分类表 ods_sub_category，存储从 MySQL 同步的子分类及所属分类原始数据"""

    __tablename__ = "ods_sub_category"
    id = Column(types.Int64, primary_key=True)
    name = Column(types.String)
    category_id = Column(types.Int64)
    create_time = Column(types.DateTime)
    update_time = Column(types.DateTime)
