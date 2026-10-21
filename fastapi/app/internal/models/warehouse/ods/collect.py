from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class OdsCollect(WarehouseModel):
    """ClickHouse ODS 层收藏表 ods_collects，存储从 MySQL 同步的用户收藏原始记录"""

    __tablename__ = "ods_collects"
    id = Column(types.Int64, primary_key=True)
    article_id = Column(types.Int64)
    user_id = Column(types.Int64)
    created_time = Column(types.DateTime)
