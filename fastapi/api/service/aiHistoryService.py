from functools import lru_cache
from typing import Any
import hashlib
import time
from fastapi import Depends
from api.mapper import AiHistoryMapper, get_ai_history_mapper
from entity.po import AiHistory

class AiHistoryService:
    def __init__(self, ai_history_mapper: AiHistoryMapper):
        self.ai_history_mapper = ai_history_mapper
        # 用于短时间去重的缓存（生产环境建议用 Redis）
        self._request_cache = {}
        
    def create_ai_history(self, ai_history: Any, db: Any) -> Any:
        data = ai_history.dict() if hasattr(ai_history, "dict") else dict(ai_history)

        # 方案1：基于内容和用户ID生成唯一键进行去重（5秒内相同请求只处理一次）
        request_key = hashlib.md5(
            f"{data['user_id']}:{data['ask']}:{data['reply']}".encode()
        ).hexdigest()
        
        current_time = time.time()
        if request_key in self._request_cache:
            last_time = self._request_cache[request_key]
            if current_time - last_time < 5:  # 5秒内的重复请求
                return {"status": "duplicate", "message": "请求正在处理中"}
        
        self._request_cache[request_key] = current_time
        
        # 清理过期缓存（保留最近10秒的记录）
        self._request_cache = {
            k: v for k, v in self._request_cache.items() 
            if current_time - v < 10
        }

        history = AiHistory(
            user_id=data["user_id"],
            ask=data["ask"],
            reply=data["reply"],
            ai_type=data["ai_type"]
        )
        
        return self.ai_history_mapper.create_ai_history(history, db)

    def get_all_ai_history(self, user_id: int, db: Any) -> list[AiHistory]:
        data = self.ai_history_mapper.get_all_ai_history_by_userid(db, user_id=user_id, limit=None)
        # 格式化时间为 "YYYY-MM-DD HH:MM:SS"
        fmt = "%Y-%m-%d %H:%M:%S"
        for item in data:
            if getattr(item, "created_at", None):
                try:
                    item.created_at = item.created_at.strftime(fmt)
                except Exception:
                    pass
            if getattr(item, "updated_at", None):
                try:
                    item.updated_at = item.updated_at.strftime(fmt)
                except Exception:
                    pass
        return data
    
    def delete_ai_history_by_userid(self, user_id: int, db: Any) -> None:
        self.ai_history_mapper.delete_ai_history_by_userid(db, user_id)

    
@lru_cache
def get_ai_history_service(ai_history_mapper: AiHistoryMapper = Depends(get_ai_history_mapper)) -> AiHistoryService:
    return AiHistoryService(ai_history_mapper)