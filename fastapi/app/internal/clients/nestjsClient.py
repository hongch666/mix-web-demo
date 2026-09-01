from typing import Any, Optional

from app.core.client import call_remote_service
from app.core.config import load_config


class NestjsClient:
    """NestJS 服务客户端"""

    SERVICE_NAME: str = "nestjs"

    async def get_api_average_speed(self) -> Any:
        """远程调用 NestJS 获取所有接口的平均响应速度"""
        result: dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/api-logs/average-speed",
            method="GET",
        )
        return result.get("data", [])

    async def get_called_count(self) -> Any:
        """远程调用 NestJS 获取接口调用次数"""
        result: dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/api-logs/called-count",
            method="GET",
        )
        return result.get("data", [])

    async def get_article_view_distribution(self, user_id: int) -> Any:
        """远程调用 NestJS 获取用户文章浏览分布"""
        result: dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path=f"/article-logs/view-distribution/{user_id}",
            method="GET",
        )
        return result.get("data", {"total_views": 0, "articles": []})

    async def get_search_keywords(self) -> Any:
        """远程调用 NestJS 获取所有搜索关键词"""
        result: dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/article-logs/search-keywords",
            method="GET",
        )
        return result.get("data", [])

    async def list_mongodb_collections(self) -> Any:
        """远程调用 NestJS 列出日志集合"""
        result: dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/mongo-tools/collections",
            method="GET",
        )
        return result.get("data", [])

    async def query_mongodb(
        self, collection_name: str, filter_dict: Optional[dict[str, Any]], limit: int
    ) -> Any:
        """远程调用 NestJS 查询日志集合"""
        result: dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/mongo-tools/query",
            method="POST",
            json={
                "collection_name": collection_name,
                "filter": filter_dict or {},
                "limit": limit,
            },
        )
        return result.get("data", [])

    async def sync_article_logs(
        self, cursor: str = "", limit: int = 1000
    ) -> dict[str, Any]:
        """通过 NestJS 内部接口按 MongoDB ID 游标同步文章日志"""
        result: dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/article-logs/sync",
            method="GET",
            params={"cursor": cursor, "limit": limit},
        )
        return result.get("data", {"list": [], "nextCursor": None})

    async def upload_file(self, file_path: str, oss_path: str) -> dict[str, Any]:
        """远程调用 NestJS 上传文件到 OSS"""
        remote_call_config: dict[str, Any] = load_config("remote_call")
        upload_timeout: int = int(remote_call_config.get("upload_timeout", 300))
        max_retries: int = int(remote_call_config.get("max_retries", 3))
        return await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/upload",
            method="POST",
            json={
                "local_file": file_path,
                "oss_file": oss_path,
            },
            retries=max_retries,
            timeout=upload_timeout,
        )

    # ==================== SQL 代理接口（供 FastAPI Agent 远程调用） ====================

    async def get_tables(self, table: Optional[str] = None) -> Any:
        """获取 MySQL 表结构信息"""
        params = {"table": table} if table else None
        result: dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/sql-tools/tables",
            method="GET",
            params=params,
        )
        return result.get("data", [])

    async def execute_query(
        self, query: str, params: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """执行只读参数化 SQL 查询"""
        result: dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/sql-tools/query",
            method="POST",
            json={"query": query, "params": params or {}},
        )
        return result.get("data", {})
