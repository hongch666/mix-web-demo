from typing import List, Any
from pydantic import BaseModel

class ListResponse(BaseModel):
    total: int
    list: List[Any]