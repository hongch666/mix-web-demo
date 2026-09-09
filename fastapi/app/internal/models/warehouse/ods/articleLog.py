from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class OdsArticleLog(WarehouseModel):
    __tablename__ = "ods_article_log"
    event_id = Column(types.String, primary_key=True)
    user_id = Column(types.Int64)
    article_id = Column(types.Int64)
    action = Column(types.String)
    content = Column(types.String)
    created_at = Column(types.DateTime)
