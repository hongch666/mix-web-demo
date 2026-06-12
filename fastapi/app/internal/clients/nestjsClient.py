from typing import Any, Dict

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
            timeout=300,
        )
