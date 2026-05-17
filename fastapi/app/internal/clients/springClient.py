from typing import Any, Dict, List, Optional

from app.core.client import call_remote_service


class SpringClient:
    """Spring 服务客户端"""

    SERVICE_NAME: str = "spring"

    async def test(self) -> Dict[str, Any]:
        """测试 Spring 服务连通性"""
        return await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/api_spring/spring",
            method="GET",
            retries=2,
        )

    async def get_top_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        result = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/articles/analyze/top",
            method="GET",
            params={"limit": limit},
        )
        return result.get("data", [])

    async def get_article_statistics(self) -> Dict[str, Any]:
        result = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/articles/analyze/statistics",
            method="GET",
        )
        return result.get("data", {})

    async def get_category_article_count(self) -> List[Dict[str, Any]]:
        result = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/articles/analyze/category-article-count",
            method="GET",
        )
        return result.get("data", [])

    async def get_monthly_publish_count(self, months: int = 6) -> List[Dict[str, Any]]:
        result = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/articles/analyze/monthly-publish-count",
            method="GET",
            params={"months": months},
        )
        return result.get("data", [])

    async def get_export_rows(
        self, cursor: int = 0, size: int = 500
    ) -> Dict[str, Any]:
        result = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/articles/export",
            method="GET",
            params={"cursor": cursor, "size": size},
        )
        return result.get("data", {})

    async def get_ai_comment_context(self, article_id: int) -> Optional[Dict[str, Any]]:
        result = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path=f"/articles/ai-comment-context/{article_id}",
            method="GET",
        )
        return result.get("data")

    async def replace_ai_comments(
        self, article_id: int, comments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/comments/ai/replace",
            method="POST",
            json={"articleId": article_id, "comments": comments},
        )

    async def get_table_schema(self, table_name: str = "") -> Dict[str, Any]:
        result = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/agent/tables",
            method="GET",
            params={"name": table_name} if table_name else {},
            retries=1,
            timeout=5,
        )
        return result.get("data", {})

    async def execute_sql_query(
        self, sql: str, user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {"sql": sql}
        if user_id is not None:
            body["user_id"] = user_id
        result = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/agent/query",
            method="POST",
            json=body,
            retries=1,
            timeout=5,
        )
        return result.get("data", {})
