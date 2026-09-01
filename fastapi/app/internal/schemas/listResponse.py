from typing import Any

from pydantic import BaseModel


class ListResponse(BaseModel):
    """列表响应实体类"""

    total: int
    list: list[Any]
