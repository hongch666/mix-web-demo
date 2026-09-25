from __future__ import annotations

import builtins
from typing import Any

from pydantic import BaseModel, Field


class ListResponse(BaseModel):
    """列表响应实体类"""

    total: int = Field(description="总记录数")
    list: builtins.list[Any] = Field(description="列表数据")
