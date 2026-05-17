from typing import Any, Dict, Optional

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
