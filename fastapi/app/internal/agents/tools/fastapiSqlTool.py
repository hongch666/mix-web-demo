import json
import re
from functools import lru_cache
from typing import Any, Dict, List, Optional

from app.core.base import Logger
from app.core.constants import Messages, Prompts
from app.core.db import get_db
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from sqlalchemy import text


class FastapiSqlTool:
    """FastAPI 本地 MySQL 数据查询工具（直连）

    可查询的表: ai_history
    后续可能新增其他由 FastAPI 管理的表。
    """

    def __init__(self) -> None:
        self.logger = Logger
        self._user_id: Optional[int] = None

    def set_user_id(self, user_id: Optional[int]) -> None:
        """设置当前用户ID（用于权限上下文）"""
        self._user_id = user_id

    async def get_tables(self, table_name: str = "") -> str:
        """获取 FastAPI 本地 MySQL 表结构"""
        try:
            name = table_name.strip()
            whitelist = set(Messages.SQL_TOOL_FASTAPI_TABLE_WHITELIST)
            schemas = Messages.SQL_TOOL_FASTAPI_TABLE_SCHEMAS
            if name:
                if name not in whitelist:
                    return Messages.SQL_TOOL_TABLE_NOT_IN_WHITELIST(name)
                schema = schemas.get(name)
                if schema:
                    return json.dumps(
                        {"table": name, "columns": schema},
                        ensure_ascii=False,
                        indent=2,
                    )
                return f"未找到表 '{name}' 的结构信息"

            # 返回所有白名单表
            tables = [{"table": t, "columns": schemas.get(t, [])} for t in whitelist]
            return json.dumps(tables, ensure_ascii=False, indent=2)
        except Exception as e:
            error_msg = Messages.SQL_TOOL_TABLE_SCHEMA_FAILED("FastAPI", e)
            self.logger.error(error_msg)
            return error_msg

    async def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> str:
        """执行 FastAPI 本地 MySQL 只读 SQL 查询"""
        try:
            if not query or not query.strip():
                return Messages.SQL_TOOL_QUERY_EMPTY

            normalized = query.strip()
            # 安全校验
            upper = normalized.upper()
            allowed = any(
                upper.startswith(p) for p in Messages.SQL_TOOL_ALLOWED_PREFIXES
            )
            if not allowed:
                return Messages.SQL_TOOL_FORBIDDEN_STATEMENT

            # 检查表名白名单
            whitelist = set(Messages.SQL_TOOL_FASTAPI_TABLE_WHITELIST)
            table_matches = re.findall(
                r"\b(?:FROM|JOIN)\s+`?(\w+)`?", normalized, re.IGNORECASE
            )
            for t in table_matches:
                if t.lower() not in whitelist:
                    return Messages.SQL_TOOL_TABLE_NOT_IN_WHITELIST(t)

            # 检查 LIMIT
            limit_match = re.search(r"\bLIMIT\s+(\d+)", normalized, re.IGNORECASE)
            if not limit_match:
                return Messages.SQL_TOOL_LIMIT_REQUIRED
            if int(limit_match.group(1)) > Messages.SQL_TOOL_MAX_LIMIT:
                return Messages.SQL_TOOL_LIMIT_EXCEEDED

            # 检查参数化
            if ":" not in normalized:
                return Messages.SQL_TOOL_PARAM_REQUIRED

            # 执行查询
            async for session in get_db():
                result = await session.execute(text(normalized), params or {})
                rows = result.mappings().all()
                rows_list = [dict(r) for r in rows]

                if not rows_list:
                    return json.dumps(
                        {"columns": [], "rows": [], "rowCount": 0},
                        ensure_ascii=False,
                    )

                columns = list(rows_list[0].keys())
                row_values = [[row.get(col) for col in columns] for row in rows_list]
                return json.dumps(
                    {
                        "columns": columns,
                        "rows": row_values,
                        "rowCount": len(rows_list),
                    },
                    ensure_ascii=False,
                    default=str,
                )
            return Messages.SQL_TOOL_DB_SESSION_UNAVAILABLE
        except Exception as e:
            error_msg = Messages.SQL_TOOL_QUERY_FAILED("FastAPI", e)
            self.logger.error(error_msg)
            return error_msg

    def get_langchain_tools(self) -> List[StructuredTool]:
        """获取 LangChain Tool 对象列表"""

        class GetFastapiTableSchemaInput(BaseModel):
            table_name: str = Field(
                default="",
                description=Messages.SQL_TOOL_TABLE_SCHEMA_INPUT_DESC,
            )

        class ExecuteFastapiSqlQueryInput(BaseModel):
            query: str = Field(description=Messages.SQL_TOOL_QUERY_INPUT_DESC)
            params: Dict[str, Any] = Field(
                default_factory=dict,
                description=Messages.SQL_TOOL_PARAMS_INPUT_DESC,
            )

        return [
            StructuredTool(
                name=Messages.SQL_TOOL_FASTAPI_TABLE_TOOL_NAME,
                description=Prompts.FASTAPI_SQL_TABLE_TOOL_DESC,
                coroutine=self.get_tables,
                args_schema=GetFastapiTableSchemaInput,
            ),
            StructuredTool(
                name=Messages.SQL_TOOL_FASTAPI_QUERY_TOOL_NAME,
                description=Prompts.FASTAPI_SQL_QUERY_TOOL_DESC,
                coroutine=self.execute_query,
                args_schema=ExecuteFastapiSqlQueryInput,
            ),
        ]


@lru_cache
def get_fastapi_sql_tool() -> FastapiSqlTool:
    """获取 FastAPI SQL 工具实例"""
    return FastapiSqlTool()
