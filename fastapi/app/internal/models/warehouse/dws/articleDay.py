from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class DwsArticleDay(WarehouseModel):
    """ClickHouse 汇总层表 dws_article_day，按日与文章维度汇总浏览、点赞、收藏与评论量"""

    __tablename__ = "dws_article_day"
    stat_date = Column(types.Date, primary_key=True)
    article_id = Column(types.Int64, primary_key=True)
    user_id = Column(types.Int64)
    parent_category_id = Column(types.Int64)
    views = Column(types.Int64)
    like_count = Column(types.Int64)
    collect_count = Column(types.Int64)
    comment_count = Column(types.Int64)
    view_count = Column(types.Int64)
