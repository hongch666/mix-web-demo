from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class AdsUserViewArticle(WarehouseModel):
    __tablename__ = "ads_user_view_articles"
    user_id = Column(types.Int64, primary_key=True)
    article_id = Column(types.Int64, primary_key=True)
    article_title = Column(types.String)
    view_count = Column(types.Int64)
    stat_time = Column(types.DateTime)
