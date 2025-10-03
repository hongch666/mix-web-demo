from pydantic import BaseModel

class CreateHistoryDTO(BaseModel):
    user_id: int
    ask: str
    reply: str
    ai_type: str