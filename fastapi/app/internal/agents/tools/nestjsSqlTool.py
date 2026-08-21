import json
from functools import lru_cache
from typing import Any, Dict, List, Optional

from app.core.base import Logger
from app.core.constants import Messages, Prompts
from app.internal.clients import NestjsClient
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class NestjsSqlTool:
    """NestJS 服务 SQL 查询工具（远程代理）"""

    def __init__(self) -> None:
        self.logger = Logger
        self._client: NestjsClient = NestjsClient()

    async def get_tables(self, table_name: str = "") -> str:
        """获取 NestJS 侧 MySQL 表结构"""
        try:
            table_param = table_name.strip() if table_name else None
            result: Any = await self._client.get_tables(table_param)
            if not result:
                return Messages.SQL_TOOL_NO_TABLE_SCHEMA
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            error_msg = Messages.SQL_TOOL_TABLE_SCHEMA_FAILED("NestJS", e)
            self.logger.error(error_msg)
            return error_msg

    async def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> str:
        """执行 NestJS 侧只读 SQL 查询"""
        try:
            if not query or not query.strip():
                return Messages.SQL_TOOL_QUERY_EMPTY
            result: Dict[str, Any] = await self._client.execute_query(query, params)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            error_msg = Messages.SQL_TOOL_QUERY_FAILED("NestJS", e)
            self.logger.error(error_msg)
            return error_msg

    def get_langchain_tools(self) -> List[StructuredTool]:
        """获取 LangChain Tool 对象列表"""

        class GetNestjsTableSchemaInput(BaseModel):
            table_name: str = Field(
                default="",
                description=Messages.SQL_TOOL_TABLE_SCHEMA_INPUT_DESC,
            )

        class ExecuteNestjsSqlQueryInput(BaseModel):
            query: str = Field(description=Messages.SQL_TOOL_QUERY_INPUT_DESC)
            params: Dict[str, Any] = Field(
                default_factory=dict,
                description=Messages.SQL_TOOL_PARAMS_INPUT_DESC,
            )

        return [
            StructuredTool(
                name=Messages.SQL_TOOL_NESTJS_TABLE_TOOL_NAME,
                description=Prompts.NESTJS_SQL_TABLE_TOOL_DESC,
                coroutine=self.get_tables,
                args_schema=GetNestjsTableSchemaInput,
            ),
            StructuredTool(
                name=Messages.SQL_TOOL_NESTJS_QUERY_TOOL_NAME,
                description=Prompts.NESTJS_SQL_QUERY_TOOL_DESC,
                coroutine=self.execute_query,
                args_schema=ExecuteNestjsSqlQueryInput,
            ),
        ]


@lru_cache
def get_nestjs_sql_tool() -> NestjsSqlTool:
    """获取 NestJS SQL 工具实例"""
    return NestjsSqlTool()
