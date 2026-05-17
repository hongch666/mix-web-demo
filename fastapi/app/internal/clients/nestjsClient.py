from typing import Any, Dict, List

from app.core.client import call_remote_service


class NestjsClient:
    """NestJS 服务客户端"""

    SERVICE_NAME: str = "nestjs"

    async def test(self) -> Dict[str, Any]:
        """测试 NestJS 服务连通性"""
        return await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/api_nestjs/nestjs",
            method="GET",
            retries=2,
        )

    async def upload_file(self, file_path: str, oss_path: str) -> Dict[str, Any]:
        """远程调用 NestJS 上传文件到 OSS"""
        return await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/upload",
            method="POST",
            json={
                "local_file": file_path,
                "oss_file": oss_path,
            },
            retries=3,
        )

    async def get_api_average_speed(self) -> List[Dict[str, Any]]:
        result = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/api-logs/average-speed",
            method="GET",
        )
        return result.get("data", [])

    async def get_called_count_apis(self) -> List[Dict[str, Any]]:
        result = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/api-logs/called-count",
            method="GET",
        )
        return result.get("data", [])

    async def get_search_keywords(self) -> List[str]:
        result = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/article-logs/search-keywords",
            method="GET",
        )
        data: Dict[str, Any] = result.get("data", {})
        return data.get("keywords", [])

    async def get_view_distribution(self, user_id: int) -> Dict[str, Any]:
        result = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/article-logs/view-distribution",
            method="GET",
            params={"userId": user_id},
        )
        return result.get("data", {})

    async def list_log_collections(self) -> Dict[str, Any]:
        result = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/agent/log-collections",
            method="GET",
            retries=1,
            timeout=5,
        )
        return result.get("data", {})

    async def query_log(
        self,
        collection: str,
        filter_dict: Dict[str, Any] | None = None,
        limit: int = 10,
        sort: Dict[str, int] | None = None,
    ) -> Dict[str, Any]:
        result = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/agent/log-query",
            method="POST",
            json={
                "collection": collection,
                "filter": filter_dict or {},
                "limit": limit,
                "sort": sort or {"createdAt": -1},
            },
            retries=1,
            timeout=5,
        )
        return result.get("data", {})
