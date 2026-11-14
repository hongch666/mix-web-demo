from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class AdsSearchKeyword(WarehouseModel):
    """ClickHouse ADS 层搜索关键词表 ads_search_keywords，记录搜索热词、搜索次数及统计时间"""

    __tablename__ = "ads_search_keywords"
    keyword = Column(types.String, primary_key=True)
    search_count = Column(types.UInt64)
    stat_time = Column(types.DateTime)
