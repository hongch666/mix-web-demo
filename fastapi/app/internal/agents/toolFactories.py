from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.internal.crud import get_vector_embeddings, get_vector_store_mapper

from .tools.fastapiSqlTool import get_fastapi_sql_tool
from .tools.gozeroSqlTool import get_gozero_sql_tool
from .tools.mongoDBTools import get_mongodb_tools
from .tools.neo4jTools import get_neo4j_tools
from .tools.nestjsSqlTool import get_nestjs_sql_tool
from .tools.ragTools import RAGTools, get_rag_tools
from .tools.springSqlTool import get_spring_sql_tool
from .tools.warehouseTools import get_warehouse_tools


def _default_rag_tools() -> RAGTools:
    """RAG 工具默认装配，自行解析向量库 Mapper 单例"""
    return get_rag_tools(get_vector_store_mapper(get_vector_embeddings()))


@dataclass(frozen=True)
class AgentToolFactories:
    """Agent 工具组的装配工厂集合

    以工厂而非实例形式传递，使 initialize_ai_tools 仍能按组并行加载，
    并在单个工具组装配失败时隔离故障、保留其余工具
    """

    sql_tools: tuple[tuple[str, Callable[[], Any]], ...]
    rag: tuple[str, Callable[[], Any]]
    neo4j: tuple[str, Callable[[], Any]]
    mongodb: tuple[str, Callable[[], Any]]
    warehouse: tuple[str, Callable[[], Any]]


def default_agent_tool_factories() -> AgentToolFactories:
    """默认装配：各工具工厂自行解析客户端单例

    用于不经依赖图构建 AI 服务的场景（如手工构造、脚本、测试）
    """
    return AgentToolFactories(
        sql_tools=(
            ("FastAPI", get_fastapi_sql_tool),
            ("Spring", get_spring_sql_tool),
            ("GoZero", get_gozero_sql_tool),
            ("NestJS", get_nestjs_sql_tool),
        ),
        rag=("RAG", _default_rag_tools),
        neo4j=("Neo4j 知识图谱", get_neo4j_tools),
        mongodb=("MongoDB 日志", get_mongodb_tools),
        warehouse=("ClickHouse 数仓", get_warehouse_tools),
    )
