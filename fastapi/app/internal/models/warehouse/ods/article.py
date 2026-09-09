from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class OdsArticle(WarehouseModel):
    __tablename__ = "ods_articles"
    id = Column(types.Int64, primary_key=True)
    title = Column(types.String)
    user_id = Column(types.Int64)
    sub_category_id = Column(types.Int64)
    tags = Column(types.String)
    status = Column(types.Int8)
    views = Column(types.Int32)
    create_at = Column(types.DateTime)
    update_at = Column(types.DateTime)
