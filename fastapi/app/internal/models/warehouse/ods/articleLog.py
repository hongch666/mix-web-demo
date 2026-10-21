from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class OdsArticleLog(WarehouseModel):
    """ClickHouse ODS 层文章行为日志表 ods_article_log，存储从 MongoDB 同步的文章操作原始记录"""

    __tablename__ = "ods_article_log"
    event_id = Column(types.String, primary_key=True)
    user_id = Column(types.Int64)
    article_id = Column(types.Int64)
    action = Column(types.String)
    content = Column(types.String)
    created_at = Column(types.DateTime)
