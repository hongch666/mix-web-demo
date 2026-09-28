from __future__ import annotations

import builtins
from typing import TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ListResponse[T](BaseModel):
    """列表响应实体类"""

    total: int = Field(description="总记录数")
    list: builtins.list[T] = Field(description="列表数据")
