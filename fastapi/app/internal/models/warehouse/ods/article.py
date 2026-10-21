from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class OdsArticle(WarehouseModel):
    """ClickHouse ODS 层文章表 ods_articles，存储从 MySQL 同步的文章原始快照"""

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
