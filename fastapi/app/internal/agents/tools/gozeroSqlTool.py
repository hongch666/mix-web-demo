import json
from functools import lru_cache
from typing import Any, Dict, List, Optional

from app.core.base import Logger
from app.core.constants import Messages, Prompts
from app.internal.clients import GozeroClient
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class GozeroSqlTool:
    """GoZero 服务 SQL 查询工具（远程代理）"""

    def __init__(self) -> None:
        self.logger = Logger
        self._client: GozeroClient = GozeroClient()

    async def get_tables(self, table_name: str = "") -> str:
        """获取 GoZero 侧 MySQL 表结构"""
        try:
            table_param = table_name.strip() if table_name else None
            result: Any = await self._client.get_tables(table_param)
            if not result:
                return Messages.SQL_TOOL_NO_TABLE_SCHEMA
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            error_msg = Messages.SQL_TOOL_TABLE_SCHEMA_FAILED("GoZero", e)
            self.logger.error(error_msg)
            return error_msg

    async def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> str:
        """执行 GoZero 侧只读 SQL 查询"""
        try:
            if not query or not query.strip():
                return Messages.SQL_TOOL_QUERY_EMPTY
            result: Dict[str, Any] = await self._client.execute_query(query, params)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            error_msg = Messages.SQL_TOOL_QUERY_FAILED("GoZero", e)
            self.logger.error(error_msg)
            return error_msg

    def get_langchain_tools(self) -> List[StructuredTool]:
        """获取 LangChain Tool 对象列表"""

        class GetGozeroTableSchemaInput(BaseModel):
            table_name: str = Field(
                default="",
                description=Messages.SQL_TOOL_TABLE_SCHEMA_INPUT_DESC,
            )

        class ExecuteGozeroSqlQueryInput(BaseModel):
            query: str = Field(description=Messages.SQL_TOOL_QUERY_INPUT_DESC)
            params: Dict[str, Any] = Field(
                default_factory=dict,
                description=Messages.SQL_TOOL_PARAMS_INPUT_DESC,
            )

        return [
            StructuredTool(
                name=Messages.SQL_TOOL_GOZERO_TABLE_TOOL_NAME,
                description=Prompts.GOZERO_SQL_TABLE_TOOL_DESC,
                coroutine=self.get_tables,
                args_schema=GetGozeroTableSchemaInput,
            ),
            StructuredTool(
                name=Messages.SQL_TOOL_GOZERO_QUERY_TOOL_NAME,
                description=Prompts.GOZERO_SQL_QUERY_TOOL_DESC,
                coroutine=self.execute_query,
                args_schema=ExecuteGozeroSqlQueryInput,
            ),
        ]


@lru_cache
def get_gozero_sql_tool() -> GozeroSqlTool:
    """获取 GoZero SQL 工具实例"""
    return GozeroSqlTool()
