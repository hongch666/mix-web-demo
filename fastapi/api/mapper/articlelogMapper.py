from functools import lru_cache
from typing import Any, Dict, List
from common.client import call_remote_service

class ArticleLogMapper:

    async def get_search_keywords_articlelog_mapper(self) -> List[str]:
        # 使用NestJS部分获取日志数据
        result = await call_remote_service(
            service_name="nestjs",
            path="/logs/list",
            method="GET",
            params={"action": "search"},
        )
        logs = result["data"]["list"]
        
        all_keywords: List[str] = []
        for log in logs:
            content: Dict[str, Any] = log.get('content', {})
            if 'Keyword' in content:
                if content['Keyword'] == "":
                    continue
                all_keywords.append(content['Keyword'])
        return all_keywords

    async def get_all_articlelogs_limit_mapper(self) -> List[Dict[str, Any]]:
        # 使用NestJS部分获取日志数据
        result = await call_remote_service(
            service_name="nestjs",
            path="/logs/list",
            method="GET",
        )
        logs = result["data"]["list"]
        return logs

@lru_cache()
def get_articlelog_mapper() -> ArticleLogMapper:
    return ArticleLogMapper()