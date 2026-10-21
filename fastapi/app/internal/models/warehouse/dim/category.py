from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class DimCategory(WarehouseModel):
    """ClickHouse 维度表 dim_category，存储子分类与所属父分类的映射关系"""

    __tablename__ = "dim_category"
    sub_category_id = Column(types.Int64, primary_key=True)
    sub_category_name = Column(types.String)
    parent_category_id = Column(types.Int64)
    parent_category_name = Column(types.String)
    update_time = Column(types.DateTime)
