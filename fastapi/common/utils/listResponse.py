from typing import List, Any
from pydantic import BaseModel

class ListResponse(BaseModel):
    """列表响应实体类"""
    
    total: int
    list: List[Any]