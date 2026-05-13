from typing import Any, Dict

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
