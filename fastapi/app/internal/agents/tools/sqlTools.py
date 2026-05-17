import asyncio
import contextvars
import re
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional

from app.core.base import Constants
from app.core.db import engine
from app.internal.clients import GoZeroClient, SpringClient
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

user_id_context: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar(
    "user_id", default=None
)

AI_HISTORY_TABLES: set[str] = {"ai_history"}
LOCAL_SOURCE = "fastapi_local"
SPRING_SOURCE = "spring"
GOZERO_SOURCE = "gozero"
SCHEMA_CACHE_TTL = 300
_TABLE_SCHEMA_CACHE: Dict[str, tuple[float, str]] = {}


class SQLTools:
    """多数据源 SQL 查询工具"""

    def __init__(self) -> None:
        from app.core.base import Logger

        self.logger = Logger
        self.engine = engine
        self.spring_client = SpringClient()
        self.gozero_client = GoZeroClient()
        self.logger.info(Constants.SQL_MULTI_SOURCE_INITIALIZED_MESSAGE)

    def set_user_id(self, user_id: Optional[int]) -> None:
        if user_id:
            user_id_context.set(user_id)
            self.logger.info(
                Constants.SQL_SET_USER_ID_MESSAGE.format(user_id=user_id)
            )

    def get_user_id(self) -> Optional[int]:
        return user_id_context.get()

    @staticmethod
    def _strip_sql_comments(sql: str) -> str:
        sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
        sql = re.sub(r"(?m)--[^\n]*$", " ", sql)
        sql = re.sub(r"(?m)#[^\n]*$", " ", sql)
        return sql

    @staticmethod
    def _strip_sql_strings(sql: str) -> str:
        sql = re.sub(r"'([^'\\\\]|\\\\.)*'", "''", sql)
        sql = re.sub(r'"([^"\\\\]|\\\\.)*"', '""', sql)
        return sql

    def _normalize_sql_for_validation(self, query: str) -> str:
        sql = self._strip_sql_comments(query or "")
        sql = self._strip_sql_strings(sql)
        return re.sub(r"\s+", " ", sql.strip()).upper()

    @staticmethod
    def _clean_tool_input(text: str) -> str:
        cleaned = (text or "").strip()
        cleaned = re.split(r"\b(?:Observation|Thought|Final Answer)\s*:", cleaned)[0]
        cleaned = cleaned.strip().strip('"').strip("'").strip("`")
        return cleaned.strip()

    @staticmethod
    def _extract_table_names(sql: str) -> List[str]:
        matches = re.findall(
            r"\b(?:FROM|JOIN|UPDATE|INTO|TABLE|DESC|DESCRIBE)\s+[`'\"]?([A-Za-z_][A-Za-z0-9_]*)[`'\"]?",
            sql,
            re.IGNORECASE,
        )
        return list({SQLTools._normalize_table_name(table) for table in matches})

    @staticmethod
    def _normalize_table_name(table_name: str) -> str:
        cleaned = table_name.strip().strip("`\"'").lower()
        if cleaned == "users":
            return "user"
        return cleaned

    def _normalize_known_table_names(self, query: str) -> str:
        def replace_table(match: re.Match[str]) -> str:
            keyword = match.group(1)
            table_name = self._normalize_table_name(match.group(2))
            return f"{keyword}{table_name}"

        return re.sub(
            r"\b(FROM\s+|JOIN\s+)([`\"']?[A-Za-z_][A-Za-z0-9_]*[`\"']?)",
            replace_table,
            query,
            flags=re.IGNORECASE,
        )

    def _is_read_only_query(self, query: str) -> tuple[bool, str]:
        normalized_sql = self._normalize_sql_for_validation(query)
        if not normalized_sql:
            return False, Constants.SQL_TOOL_LIMIT

        sql_without_trailing_semicolon = normalized_sql.rstrip(";").strip()
        if not sql_without_trailing_semicolon:
            return False, Constants.SQL_TOOL_LIMIT
        if ";" in sql_without_trailing_semicolon:
            return False, Constants.SQL_QUERY_MULTIPLE_STATEMENTS_ERROR

        if not any(
            sql_without_trailing_semicolon.startswith(prefix)
            for prefix in Constants.SQL_READONLY_ALLOWED_PREFIXES
        ):
            return False, Constants.SQL_TOOL_LIMIT

        for keyword in Constants.SQL_DANGEROUS_KEYWORDS:
            if re.search(rf"\b{re.escape(keyword)}\b", sql_without_trailing_semicolon):
                return False, Constants.SQL_QUERY_WRITE_OPERATION_ERROR

        for pattern in Constants.SQL_DANGEROUS_PATTERNS:
            if pattern in sql_without_trailing_semicolon:
                return False, Constants.SQL_QUERY_WRITE_OPERATION_ERROR

        return True, ""

    def is_dangerous_nl_request(self, question: str) -> bool:
        normalized_question = re.sub(r"\s+", " ", (question or "")).strip().lower()
        if not normalized_question:
            return False
        return any(
            re.search(pattern, normalized_question, flags=re.IGNORECASE)
            for pattern in Constants.DANGEROUS_SQL_REQUEST_PATTERNS
        )

    async def get_table_schema_async(self, table_name: str = "") -> str:
        table_name = self._normalize_table_name(self._clean_tool_input(table_name))
        cached = self._get_cached_schema(table_name)
        if cached:
            return cached

        results = await asyncio.gather(
            self._fetch_local_schema(table_name),
            self._fetch_remote_schema(SPRING_SOURCE, table_name),
            self._fetch_remote_schema(GOZERO_SOURCE, table_name),
            return_exceptions=True,
        )
        schema_text = self._merge_schema_results(table_name, results)
        self._set_cached_schema(table_name, schema_text)
        return schema_text

    async def execute_query_async(self, query: str) -> str:
        query = self._clean_tool_input(query)
        query = self._normalize_known_table_names(query)
        is_safe, error_message = self._is_read_only_query(query)
        if not is_safe:
            return error_message

        current_user_id = self.get_user_id()
        results = await asyncio.gather(
            self._execute_local_query(query),
            self._execute_remote_query(SPRING_SOURCE, query, current_user_id),
            self._execute_remote_query(GOZERO_SOURCE, query, current_user_id),
            return_exceptions=True,
        )
        return self._select_and_format_query_result(results)

    def get_table_schema(self, table_name: str = "") -> str:
        return self._run_async_tool(self.get_table_schema_async(table_name))

    def execute_query(self, query: str) -> str:
        return self._run_async_tool(self.execute_query_async(query))

    def get_langchain_tools(self) -> List[StructuredTool]:
        class GetTableSchemaInput(BaseModel):
            table_name: str = Field(default="", description=Constants.SQL_TABLE_INPUT_DESC)

        class ExecuteSqlQueryInput(BaseModel):
            query: str = Field(description=Constants.SQL_QUERY_INPUT_DESC)

        return [
            StructuredTool(
                name=Constants.SQL_TABLE_TOOL_NAME,
                description=Constants.SQL_TABLE_TOOL_DESC,
                coroutine=self.get_table_schema_async,
                func=self.get_table_schema,
                args_schema=GetTableSchemaInput,
            ),
            StructuredTool(
                name=Constants.SQL_QUERY_TOOL_NAME,
                description=Constants.SQL_QUERY_TOOL_DESC,
                coroutine=self.execute_query_async,
                func=self.execute_query,
                args_schema=ExecuteSqlQueryInput,
            ),
        ]

    async def _fetch_local_schema(self, table_name: str) -> Dict[str, Any]:
        def load_schema() -> Dict[str, Any]:
            inspector = inspect(self.engine)
            tables = [table for table in inspector.get_table_names() if table in AI_HISTORY_TABLES]
            if table_name:
                tables = [table for table in tables if table == table_name]
            table_infos: List[Dict[str, Any]] = []
            for table in tables:
                table_infos.append(
                    {
                        "table_name": table,
                        "columns": [
                            {
                                "name": column["name"],
                                "type": str(column["type"]),
                                "nullable": column.get("nullable", True),
                                "default": column.get("default"),
                            }
                            for column in inspector.get_columns(table)
                        ],
                        "primary_key": inspector.get_pk_constraint(table).get(
                            "constrained_columns", []
                        ),
                        "indexes": [
                            {
                                "name": index.get("name"),
                                "columns": index.get("column_names", []),
                            }
                            for index in inspector.get_indexes(table)
                        ],
                    }
                )
            return {"source": LOCAL_SOURCE, "status": 200, "tables": table_infos}

        try:
            return await run_in_threadpool(load_schema)
        except Exception as e:
            return {"source": LOCAL_SOURCE, "status": 500, "error": str(e), "tables": []}

    async def _fetch_remote_schema(self, source: str, table_name: str) -> Dict[str, Any]:
        try:
            client = self.spring_client if source == SPRING_SOURCE else self.gozero_client
            data = await client.get_table_schema(table_name)
            return {
                "source": source,
                "status": 200,
                "tables": data.get("tables", []),
            }
        except Exception as e:
            return {"source": source, "status": 502, "error": str(e), "tables": []}

    async def _execute_local_query(self, query: str) -> Dict[str, Any]:
        tables = self._extract_table_names(query)
        if not self._is_local_query_allowed(query, tables):
            return {
                "source": LOCAL_SOURCE,
                "status": 403,
                "error": Constants.SQL_LOCAL_TABLE_SCOPE_ERROR,
            }

        def run_query() -> Dict[str, Any]:
            with Session(self.engine) as session:
                result = session.execute(text(self._append_limit_if_needed(query)))
                rows = result.fetchall()
                columns = list(result.keys())
                return {
                    "source": LOCAL_SOURCE,
                    "status": 200,
                    "columns": columns,
                    "rows": [
                        [str(value) if value is not None else None for value in row]
                        for row in rows[:500]
                    ],
                    "total": len(rows),
                    "error": None,
                }

        try:
            return await run_in_threadpool(run_query)
        except Exception as e:
            return {"source": LOCAL_SOURCE, "status": 500, "error": str(e)}

    async def _execute_remote_query(
        self, source: str, query: str, user_id: Optional[int]
    ) -> Dict[str, Any]:
        try:
            client = self.spring_client if source == SPRING_SOURCE else self.gozero_client
            data = await client.execute_sql_query(query, user_id)
            return {
                "source": source,
                "status": 200,
                "columns": data.get("columns", []),
                "rows": data.get("rows", []),
                "total": data.get("total_rows", 0),
                "error": None,
            }
        except Exception as e:
            return {"source": source, "status": 502, "error": str(e)}

    def _merge_schema_results(self, table_name: str, results: List[Any]) -> str:
        valid_results = [
            result for result in results if isinstance(result, dict) and result.get("status") == 200
        ]
        if table_name:
            tables = []
            for result in valid_results:
                for table in result.get("tables", []):
                    if table.get("table_name") == table_name:
                        tables.append((result.get("source"), table))
            if not tables:
                return Constants.SQL_TABLE_NOT_FOUND_MESSAGE.format(
                    table_name=table_name
                )
            return "\n\n".join(
                self._format_table_schema(source or "unknown", table) for source, table in tables
            )

        sections = []
        for result in valid_results:
            source = result.get("source", "unknown")
            tables = result.get("tables", [])
            source_name = self._source_label(source)
            lines = [
                Constants.SQL_SOURCE_TABLES_SUMMARY_MESSAGE.format(
                    source_name=source_name, count=len(tables)
                )
            ]
            for table in tables:
                columns = table.get("columns", [])
                column_names = ", ".join(str(column.get("name")) for column in columns)
                lines.append(
                    Constants.SQL_TABLE_SUMMARY_MESSAGE.format(
                        table_name=table.get("table_name"),
                        count=len(columns),
                        columns=column_names,
                    )
                )
            sections.append("\n".join(lines))
        return "\n\n".join(sections) if sections else Constants.SQL_SCHEMA_EMPTY_MESSAGE

    def _format_table_schema(self, source: str, table: Dict[str, Any]) -> str:
        lines = [
            Constants.SQL_TABLE_SCHEMA_TITLE_MESSAGE.format(
                source_name=self._source_label(source),
                table_name=table.get("table_name"),
            ),
            Constants.SQL_COLUMN_INFO_TITLE,
        ]
        for column in table.get("columns", []):
            nullable = (
                Constants.SQL_COLUMN_NULLABLE
                if column.get("nullable")
                else Constants.SQL_COLUMN_NOT_NULLABLE
            )
            line = f"  - {column.get('name')}: {column.get('type')} ({nullable})"
            if column.get("default") is not None:
                line += Constants.SQL_COLUMN_DEFAULT_MESSAGE.format(
                    default=column.get("default")
                )
            lines.append(line)
        primary_key = table.get("primary_key") or []
        if primary_key:
            lines.append(
                Constants.SQL_PRIMARY_KEY_MESSAGE.format(
                    columns=", ".join(primary_key)
                )
            )
        indexes = table.get("indexes") or []
        if indexes:
            lines.append(Constants.SQL_INDEX_TITLE)
            for index in indexes:
                lines.append(
                    f"  - {index.get('name')}: {', '.join(index.get('columns') or [])}"
                )
        return "\n".join(lines)

    def _select_and_format_query_result(self, results: List[Any]) -> str:
        dict_results = [result for result in results if isinstance(result, dict)]
        success_results = [
            result for result in dict_results if result.get("status") == 200
        ]
        if not success_results:
            errors = [
                Constants.SQL_SOURCE_ERROR_MESSAGE.format(
                    source=result.get("source", "unknown"),
                    status=result.get("status"),
                    error=result.get("error"),
                )
                for result in dict_results
            ]
            exception_errors = [str(result) for result in results if isinstance(result, Exception)]
            return Constants.SQL_ALL_SOURCES_FAILED_MESSAGE + "\n".join(
                errors + exception_errors
            )

        selected = next(
            (result for result in success_results if result.get("rows")),
            success_results[0],
        )
        source = selected.get("source", "unknown")
        rows = selected.get("rows", [])
        columns = selected.get("columns", [])
        total = int(selected.get("total") or len(rows))
        if total == 0:
            return Constants.SQL_QUERY_EMPTY_WITH_SOURCE_MESSAGE.format(
                source_name=self._source_label(source)
            )

        max_rows = 500
        limited_rows = rows[:max_rows]
        result_text = Constants.SQL_QUERY_RESULT_MESSAGE.format(
            total=total, source_name=self._source_label(source)
        )
        if total > max_rows:
            result_text += Constants.SQL_QUERY_RESULT_LIMIT_MESSAGE.format(
                max_rows=max_rows
            )
        result_text += ":\n\n"
        result_text += " | ".join(str(column) for column in columns) + "\n"
        result_text += "-" * (len(columns) * 15) + "\n"
        for row in limited_rows:
            result_text += " | ".join(
                str(value) if value is not None else "NULL" for value in row
            )
            result_text += "\n"
        return result_text

    @staticmethod
    def _append_limit_if_needed(query: str) -> str:
        normalized = query.strip().rstrip(";")
        if re.match(r"^\s*(SELECT|WITH)\b", normalized, flags=re.IGNORECASE) and not re.search(
            r"\bLIMIT\b", normalized, flags=re.IGNORECASE
        ):
            return f"{normalized} LIMIT 500"
        return normalized

    @staticmethod
    def _is_local_query_allowed(query: str, tables: List[str]) -> bool:
        if tables:
            return all(table in AI_HISTORY_TABLES for table in tables)

        normalized = query.strip().upper()
        return normalized.startswith(("SELECT", "WITH", "EXPLAIN SELECT", "EXPLAIN WITH"))

    @staticmethod
    def _source_label(source: str) -> str:
        return {
            LOCAL_SOURCE: "FastAPI(ai_history)",
            SPRING_SOURCE: "Spring(核心业务库)",
            GOZERO_SOURCE: "GoZero(chat_messages)",
        }.get(source, source)

    @staticmethod
    def _get_cached_schema(table_name: str) -> Optional[str]:
        key = f"schema:{table_name}" if table_name else "schema:all"
        cached = _TABLE_SCHEMA_CACHE.get(key)
        if not cached:
            return None
        timestamp, value = cached
        if time.monotonic() - timestamp < SCHEMA_CACHE_TTL:
            return value
        return None

    @staticmethod
    def _set_cached_schema(table_name: str, value: str) -> None:
        key = f"schema:{table_name}" if table_name else "schema:all"
        _TABLE_SCHEMA_CACHE[key] = (time.monotonic(), value)

    @staticmethod
    def _run_async_tool(coro: Any) -> str:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        return Constants.SQL_ASYNC_TOOL_REQUIRED_MESSAGE


@lru_cache
def get_sql_tools() -> SQLTools:
    return SQLTools()
