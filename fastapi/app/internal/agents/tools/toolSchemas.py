from typing import Optional

from pydantic import BaseModel, Field

from app.core.base import JsonArrayArgument, JsonObjectArgument
from app.core.constants import Defaults, WarehouseScripts

# 数仓工具的数据集名参数类型，当前以字符串开放，取值由工具内部按清单校验
WarehouseDataset = str


class EmptyInput(BaseModel):
    """无参数工具的参数模型"""


class TableSchemaInput(BaseModel):
    """表结构查询工具的参数模型，table_name 指定要查询的表名"""

    table_name: str = Field(
        default="",
        description="表名，留空则返回所有白名单表",
    )


class SqlQueryInput(BaseModel):
    """SQL 查询工具的参数模型，包含 SQL 语句与可选参数字典"""

    query: str = Field(description="完整的只读 SQL 查询语句")
    params: JsonObjectArgument = Field(
        default_factory=dict,
        description="参数化查询参数，对象形式的键值对，不要写成字符串",
    )


class CustomCypherInput(BaseModel):
    """自定义 Cypher 查询工具的参数模型，cypher_query 为要执行的语句"""

    cypher_query: str = Field(description="只读 Cypher 查询语句")


class MongoAggregateInput(BaseModel):
    """MongoDB 聚合工具的参数模型，包含集合名、聚合管道与返回条数上限"""

    collection_name: str = Field(description="collection 的名称")
    # 管道形态由工具内部校验：pydantic 的英文报错不如本地中文提示便于模型自纠
    pipeline: JsonArrayArgument = Field(
        description="聚合管道，按顺序执行的阶段数组，每项只包含一个阶段操作符"
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=Defaults.MONGODB_AGGREGATE_MAX_DOCS,
        description=(
            f"聚合结果返回条数上限，最大 {Defaults.MONGODB_AGGREGATE_MAX_DOCS}，服务端会强制收敛"
        ),
    )


class MongoQueryInput(BaseModel):
    """MongoDB 普通查询工具的参数模型，包含集合名、过滤条件与返回条数上限"""

    collection_name: str = Field(description="collection 的名称")
    filter_dict: JsonObjectArgument = Field(
        default_factory=dict,
        description="MongoDB 查询条件",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=Defaults.MONGODB_QUERY_MAX_LIMIT,
        description=(
            f"返回结果数量上限，最大 {Defaults.MONGODB_QUERY_MAX_LIMIT}，阈值条件请写入 filter_dict"
        ),
    )


def build_predefined_query_input(query_names: list[str]) -> type[BaseModel]:
    """按当前可用的预定义查询名构造图谱查询工具的参数模型"""
    available: str = ", ".join(query_names)

    class PredefinedQueryInput(BaseModel):
        """预定义图谱查询工具的参数模型，包含查询名与查询参数"""

        query_name: str = Field(description="预定义查询名称，可选值: " + available)
        params: JsonObjectArgument = Field(
            default_factory=dict,
            description='查询参数（对象），例如 {"id": 1, "name": "人工智能", "limit": 10}',
        )

    return PredefinedQueryInput


def build_warehouse_query_input() -> type[BaseModel]:
    """构造数仓查询工具的参数模型，数据集说明按支持清单动态拼接"""
    dataset_description: str = (
        "ADS 数据集名称，例如 platform_stats、top_articles、user_profile"
        "；可选值: " + ", ".join(WarehouseScripts.WAREHOUSE_AGENT_DATASETS)
    )

    class WarehouseQueryInput(BaseModel):
        """数仓查询工具的参数模型，包含数据集名、用户 ID、日期区间与返回条数"""

        dataset: WarehouseDataset = Field(description=dataset_description)
        user_id: Optional[int] = Field(
            default=None,
            description="用户 ID；查询 user_profile、user_daily_actions、user_view_articles 时必填",
        )
        start_date: Optional[str] = Field(
            default=None,
            description="用户日行为查询的日期范围，格式 YYYY-MM-DD（左闭右开）",
        )
        end_date: Optional[str] = Field(
            default=None,
            description="用户日行为查询的日期范围，格式 YYYY-MM-DD（左闭右开）",
        )
        limit: int = Field(
            default=20,
            ge=1,
            le=100,
            description="最多返回的记录数，范围 1-100",
        )

    return WarehouseQueryInput
