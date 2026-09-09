from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class AdsSearchKeyword(WarehouseModel):
    __tablename__ = "ads_search_keywords"
    keyword = Column(types.String, primary_key=True)
    stat_time = Column(types.DateTime)
