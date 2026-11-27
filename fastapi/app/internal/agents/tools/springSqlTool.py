import json
from functools import lru_cache
from typing import Any, Optional

from langchain_core.tools import StructuredTool

from app.core.base import Logger
from app.core.constants import Messages, Prompts
from app.internal.agents.permissions.toolScope import (
    enforce_sql_row_scope,
    log_scope_denial,
)
from app.internal.agents.tools.toolSchemas import SqlQueryInput, TableSchemaInput
from app.internal.clients import SpringClient


class SpringSqlTool:
    """Spring 服务 SQL 查询工具（远程代理）"""

    def __init__(self, spring_client: SpringClient) -> None:
        """初始化 Spring SQL 工具并注入 Spring 远程客户端"""
        self.logger = Logger
        self._client: SpringClient = spring_client

    async def get_tables(self, table_name: str = "") -> str:
        """获取 Spring 侧 MySQL 表结构"""
        try:
            table_param = table_name.strip() if table_name else None
            result: list[dict[str, Any]] = await self._client.get_tables(table_param)
            if not result:
                return Messages.SQL_TOOL_NO_TABLE_SCHEMA
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            error_msg = Messages.SQL_TOOL_TABLE_SCHEMA_FAILED("Spring", e)
            self.logger.error(error_msg)
            return error_msg

    async def execute_query(
        self, query: str, params: Optional[dict[str, Any]] = None
    ) -> str:
        """执行 Spring 侧只读 SQL 查询"""
        try:
            if not query or not query.strip():
                return Messages.SQL_TOOL_QUERY_EMPTY
            # 行级范围校验：非 admin 仅允许查询本人数据
            denial = enforce_sql_row_scope(query, params)
            if denial:
                log_scope_denial("SpringSqlTool", denial)
                return denial
            result: dict[str, Any] = await self._client.execute_query(query, params)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            error_msg = Messages.SQL_TOOL_QUERY_FAILED("Spring", e)
            self.logger.error(error_msg)
            return error_msg

    def get_langchain_tools(self) -> list[StructuredTool]:
        """获取 LangChain Tool 对象列表"""

        return [
            StructuredTool(
                name=Messages.SQL_TOOL_SPRING_TABLE_TOOL_NAME,
                description=Prompts.SPRING_SQL_TABLE_TOOL_DESC,
                coroutine=self.get_tables,
                args_schema=TableSchemaInput,
            ),
            StructuredTool(
                name=Messages.SQL_TOOL_SPRING_QUERY_TOOL_NAME,
                description=Prompts.SPRING_SQL_QUERY_TOOL_DESC,
                coroutine=self.execute_query,
                args_schema=SqlQueryInput,
            ),
        ]


@lru_cache
def get_spring_sql_tool(spring_client: SpringClient) -> SpringSqlTool:
    """获取 Spring SQL 工具实例"""
    return SpringSqlTool(spring_client)
