from typing import Any, Dict

from app.core.client import call_remote_service
from app.core.config import load_config


class NestjsClient:
    """NestJS 服务客户端"""

    SERVICE_NAME: str = "nestjs"

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
