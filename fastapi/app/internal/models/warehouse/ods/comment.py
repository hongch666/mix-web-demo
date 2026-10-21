from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class OdsComment(WarehouseModel):
    """ClickHouse ODS 层评论表 ods_comments，存储从 MySQL 同步的用户评论及评分原始记录"""

    __tablename__ = "ods_comments"
    id = Column(types.Int64, primary_key=True)
    user_id = Column(types.Int64)
    article_id = Column(types.Int64)
    star = Column(types.Float64)
    create_time = Column(types.DateTime)
    update_time = Column(types.DateTime)
