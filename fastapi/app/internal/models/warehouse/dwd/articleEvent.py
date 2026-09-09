from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class DwdArticleEvent(WarehouseModel):
    __tablename__ = "dwd_article_event"
    id = Column(types.Int64, primary_key=True)
    title = Column(types.String)
    user_id = Column(types.Int64)
    views = Column(types.Int32)
    status = Column(types.Int8)
    sub_category_id = Column(types.Int64)
    parent_category_id = Column(types.Int64)
    parent_category_name = Column(types.String)
    create_date = Column(types.Date)
    create_at = Column(types.DateTime)
    update_at = Column(types.DateTime)
