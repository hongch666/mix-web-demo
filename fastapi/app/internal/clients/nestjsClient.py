from typing import Any, Dict, Optional

from app.core.client import call_remote_service
from app.core.config import load_config


class NestjsClient:
    """NestJS 服务客户端"""

    SERVICE_NAME: str = "nestjs"

    async def get_api_average_speed(self) -> Any:
        """远程调用 NestJS 获取所有接口的平均响应速度"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/api-logs/average-speed",
            method="GET",
        )
        return result.get("data", [])

    async def get_called_count(self) -> Any:
        """远程调用 NestJS 获取接口调用次数"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/api-logs/called-count",
            method="GET",
        )
        return result.get("data", [])

    async def get_article_view_distribution(self, user_id: int) -> Any:
        """远程调用 NestJS 获取用户文章浏览分布"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path=f"/article-logs/view-distribution/{user_id}",
            method="GET",
        )
        return result.get("data", {"total_views": 0, "articles": []})

    async def list_mongodb_collections(self) -> Any:
        """远程调用 NestJS 列出日志集合"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/mongo-tools/collections",
            method="GET",
        )
        return result.get("data", [])

    async def query_mongodb(
        self, collection_name: str, filter_dict: Optional[Dict[str, Any]], limit: int
    ) -> Any:
        """远程调用 NestJS 查询日志集合"""
        result: Dict[str, Any] = await call_remote_service(
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

    async def upload_file(self, file_path: str, oss_path: str) -> Dict[str, Any]:
        """远程调用 NestJS 上传文件到 OSS"""
        remote_call_config: Dict[str, Any] = load_config("remote_call")
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
