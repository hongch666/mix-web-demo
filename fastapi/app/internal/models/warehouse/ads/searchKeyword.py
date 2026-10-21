from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class AdsSearchKeyword(WarehouseModel):
    """ClickHouse ADS 层搜索关键词表 ads_search_keywords，记录搜索热词及统计时间"""

    __tablename__ = "ads_search_keywords"
    keyword = Column(types.String, primary_key=True)
    stat_time = Column(types.DateTime)
