import json
from datetime import date
from functools import lru_cache
from typing import Any, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.core.base import Logger
from app.core.constants import Messages, Prompts, WarehouseScripts
from app.core.db import execute_clickhouse_query

WarehouseDataset = str


class ClickHouseWarehouseTools:
    """ClickHouse 数仓 ADS 查询工具，仅允许访问预定义聚合数据集。"""

    _USER_DATASETS: frozenset[str] = WarehouseScripts.WAREHOUSE_AGENT_USER_DATASETS

    def __init__(self) -> None:
        self.logger = Logger

    async def list_datasets(self) -> str:
        """返回数仓工具支持的数据集和适用范围。"""
        datasets: dict[str, str] = WarehouseScripts.WAREHOUSE_AGENT_DATASET_DESCRIPTIONS
        return json.dumps(datasets, ensure_ascii=False, indent=2)

    async def query_warehouse(
        self,
        dataset: WarehouseDataset,
        user_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 20,
    ) -> str:
        """执行固定 ADS 查询并返回结构化 JSON 结果。"""
        if dataset not in WarehouseScripts.WAREHOUSE_AGENT_DATASETS:
            return Messages.WAREHOUSE_DATASET_UNSUPPORTED.format(dataset=dataset)
        if dataset in self._USER_DATASETS and user_id is None:
            return Messages.WAREHOUSE_USER_ID_REQUIRED

        if start_date is not None or end_date is not None:
            try:
                if start_date:
                    date.fromisoformat(start_date)
                if end_date:
                    date.fromisoformat(end_date)
            except ValueError:
                return Messages.WAREHOUSE_DATE_INVALID

        safe_limit: int = max(1, min(int(limit), 100))
        params: dict[str, Any] = {
            "user_id": user_id,
            "start_date": start_date or "1970-01-01",
            "end_date": end_date or "2100-01-01",
            "limit": safe_limit,
        }
        query: str = WarehouseScripts.WAREHOUSE_AGENT_QUERIES[dataset]
        try:
            rows: list[Any] = await execute_clickhouse_query(query, params)
            columns: list[str] = self._result_columns(dataset)
            return json.dumps(
                {
                    "dataset": dataset,
                    "columns": columns,
                    "rows": [list(row) for row in rows],
                    "rowCount": len(rows),
                    "source": "ClickHouse ADS",
                },
                ensure_ascii=False,
                default=str,
            )
        except Exception as error:
            self.logger.error(Messages.WAREHOUSE_QUERY_FAILED.format(error=error))
            return Messages.WAREHOUSE_QUERY_FAILED.format(error=error)

    @staticmethod
    def _result_columns(dataset: str) -> list[str]:
        return WarehouseScripts.WAREHOUSE_AGENT_RESULT_COLUMNS[dataset]

    def get_langchain_tools(self) -> list[StructuredTool]:
        """获取 LangChain 数仓工具对象列表。"""

        class EmptyInput(BaseModel):
            pass

        class WarehouseQueryInput(BaseModel):
            dataset: WarehouseDataset = Field(
                description=(
                    Messages.WAREHOUSE_DATASET_INPUT_DESC
                    + "；可选值: "
                    + ", ".join(WarehouseScripts.WAREHOUSE_AGENT_DATASETS)
                )
            )
            user_id: Optional[int] = Field(
                default=None, description=Messages.WAREHOUSE_USER_ID_INPUT_DESC
            )
            start_date: Optional[str] = Field(
                default=None, description=Messages.WAREHOUSE_DATE_INPUT_DESC
            )
            end_date: Optional[str] = Field(
                default=None, description=Messages.WAREHOUSE_DATE_INPUT_DESC
            )
            limit: int = Field(
                default=20,
                ge=1,
                le=100,
                description=Messages.WAREHOUSE_LIMIT_INPUT_DESC,
            )

        return [
            StructuredTool(
                name=Messages.WAREHOUSE_LIST_DATASETS_TOOL_NAME,
                description=Prompts.CLICKHOUSE_WAREHOUSE_LIST_TOOL_DESC,
                coroutine=self.list_datasets,
                args_schema=EmptyInput,
            ),
            StructuredTool(
                name=Messages.WAREHOUSE_QUERY_TOOL_NAME,
                description=Prompts.CLICKHOUSE_WAREHOUSE_QUERY_TOOL_DESC,
                coroutine=self.query_warehouse,
                args_schema=WarehouseQueryInput,
            ),
        ]


@lru_cache
def get_warehouse_tools() -> ClickHouseWarehouseTools:
    """获取 ClickHouse 数仓工具单例。"""
    return ClickHouseWarehouseTools()
