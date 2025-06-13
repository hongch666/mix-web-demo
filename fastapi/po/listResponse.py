from typing import List, Any
from pydantic import BaseModel

class ListResponse:
    total: int
    list: List[Any]

    def __init__(self, total: int, list: List[Any]):
        self.total = total
        self.list = list