from typing import Any, Dict

from app.core.client import call_remote_service


class GoZeroClient:
    """GoZero 服务客户端"""

    SERVICE_NAME: str = "gozero"

    async def test(self) -> Dict[str, Any]:
        """测试 GoZero 服务连通性"""
        return await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/api_gozero/gozero",
            method="GET",
            retries=2,
        )
