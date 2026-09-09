from clickhouse_sqlalchemy import types
from sqlalchemy import Column

from ..base import WarehouseModel


class OdsUser(WarehouseModel):
    __tablename__ = "ods_user"
    id = Column(types.Int64, primary_key=True)
    name = Column(types.String)
    role = Column(types.String)
    img = Column(types.String)
    signature = Column(types.String)
    create_at = Column(types.DateTime)
    update_at = Column(types.DateTime)
