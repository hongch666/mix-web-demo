from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class DwdUserAction(WarehouseModel):
    """ClickHouse 明细层表 dwd_user_action，记录用户行为事件的来源对象、动作类型与时间"""

    __tablename__ = "dwd_user_action"
    event_id = Column(types.String, primary_key=True)
    source_type = Column(types.String)
    source_id = Column(types.Int64)
    action_type = Column(types.String)
    user_id = Column(types.Int64)
    article_id = Column(types.Int64)
    action_date = Column(types.Date)
    action_time = Column(types.DateTime)
