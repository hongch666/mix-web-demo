from typing import Any, Dict, Optional

from app.core.client import call_remote_service


class GozeroClient:
    """GoZero 服务客户端"""

    SERVICE_NAME: str = "gozero"

    async def get_tables(self, table: Optional[str] = None) -> Any:
        """获取 MySQL 表结构信息"""
        params = {"table": table} if table else None
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/sql-tools/tables",
            method="GET",
            params=params,
        )
        return result.get("data", [])

    async def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行只读参数化 SQL 查询"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/sql-tools/query",
            method="POST",
            json={"query": query, "params": params or {}},
        )
        return result.get("data", {})
