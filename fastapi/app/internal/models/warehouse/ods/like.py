from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class OdsLike(WarehouseModel):
    """ClickHouse ODS 层点赞表 ods_likes，存储从 MySQL 同步的用户点赞原始记录"""

    __tablename__ = "ods_likes"
    id = Column(types.Int64, primary_key=True)
    article_id = Column(types.Int64)
    user_id = Column(types.Int64)
    created_time = Column(types.DateTime)
