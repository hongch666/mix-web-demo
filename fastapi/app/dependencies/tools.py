from functools import lru_cache, partial
from typing import Annotated

from fastapi import Depends

from app.core.constants import ToolLabels
from app.internal.agents import (
    AgentToolFactories,
    ClickHouseWarehouseTools,
    FastapiSqlTool,
    GozeroSqlTool,
    MCPServerTools,
    MongoDBTools,
    Neo4jQueryTools,
    NestjsSqlTool,
    RAGTools,
    SpringSqlTool,
    get_fastapi_sql_tool,
    get_gozero_sql_tool,
    get_mcp_tools,
    get_mongodb_tools,
    get_neo4j_tools,
    get_nestjs_sql_tool,
    get_rag_tools,
    get_spring_sql_tool,
    get_warehouse_tools,
)
from app.internal.clients import GozeroClient, NestjsClient, SpringClient
from app.internal.crud import McpServerConfigMapper, VectorMapper

from .clients import GozeroClientDep, NestjsClientDep, SpringClientDep
from .mappers import McpServerConfigMapperDep, VectorMapperDep


def provide_fastapi_sql_tool() -> FastapiSqlTool:
    """装配本服务数据库的 SQL 查询工具单例，无外部依赖"""
    return get_fastapi_sql_tool()


def provide_spring_sql_tool(spring_client: SpringClientDep) -> SpringSqlTool:
    """装配 Spring 库的 SQL 查询工具单例，依赖 Spring 客户端"""
    return get_spring_sql_tool(spring_client)


def provide_gozero_sql_tool(gozero_client: GozeroClientDep) -> GozeroSqlTool:
    """装配 GoZero 库的 SQL 查询工具单例，依赖 GoZero 客户端"""
    return get_gozero_sql_tool(gozero_client)


def provide_nestjs_sql_tool(nestjs_client: NestjsClientDep) -> NestjsSqlTool:
    """装配 NestJS 库的 SQL 查询工具单例，依赖 NestJS 客户端"""
    return get_nestjs_sql_tool(nestjs_client)


def provide_mongodb_tools(nestjs_client: NestjsClientDep) -> MongoDBTools:
    """装配 MongoDB 日志查询工具单例，依赖 NestJS 客户端"""
    return get_mongodb_tools(nestjs_client)


def provide_rag_tools(vector_mapper: VectorMapperDep) -> RAGTools:
    """装配 RAG 检索工具单例，依赖向量库 Mapper"""
    return get_rag_tools(vector_mapper)


def provide_neo4j_tools() -> Neo4jQueryTools:
    """装配 Neo4j 知识图谱查询工具单例，无外部依赖"""
    return get_neo4j_tools()


def provide_warehouse_tools() -> ClickHouseWarehouseTools:
    """装配 ClickHouse 数仓查询工具单例，无外部依赖"""
    return get_warehouse_tools()


def provide_mcp_tools(mapper: McpServerConfigMapperDep) -> MCPServerTools:
    """装配 MCP 工具组工厂，工具实例在 initialize_ai_tools 中延迟构造

    构造与发现阶段读取 mcp_server_config 表；模型服务按单例复用后 MCP 工具在首次装配时发现，配置变更需清理工具工厂集合与模型服务的 lru_cache 才能重新发现
    """
    return get_mcp_tools(mapper)


@lru_cache
def build_agent_tool_factories(
    spring_client: SpringClient,
    gozero_client: GozeroClient,
    nestjs_client: NestjsClient,
    vector_mapper: VectorMapper,
    mcp_mapper: McpServerConfigMapper,
) -> AgentToolFactories:
    """按稳定依赖单例构造一次工具工厂集合，供六个模型服务的 lru_cache 命中"""
    return AgentToolFactories(
        sql_tools=(
            (ToolLabels.SQL_FASTAPI, provide_fastapi_sql_tool),
            (ToolLabels.SQL_SPRING, partial(provide_spring_sql_tool, spring_client)),
            (ToolLabels.SQL_GOZERO, partial(provide_gozero_sql_tool, gozero_client)),
            (ToolLabels.SQL_NESTJS, partial(provide_nestjs_sql_tool, nestjs_client)),
        ),
        rag=("RAG", partial(provide_rag_tools, vector_mapper)),
        neo4j=(ToolLabels.NEO4J, provide_neo4j_tools),
        mongodb=(ToolLabels.MONGODB, partial(provide_mongodb_tools, nestjs_client)),
        warehouse=(ToolLabels.WAREHOUSE, provide_warehouse_tools),
        mcp_servers=(("MCP 服务", partial(provide_mcp_tools, mcp_mapper)),),
    )


def provide_agent_tool_factories(
    spring_client: SpringClientDep,
    gozero_client: GozeroClientDep,
    nestjs_client: NestjsClientDep,
    vector_mapper: VectorMapperDep,
    mcp_mapper: McpServerConfigMapperDep,
) -> AgentToolFactories:
    """装配 agent 工具组工厂集合

    只绑定已解析的客户端单例，工具实例延迟到 initialize_ai_tools 按组并行构造，
    从而保留单组失败隔离；集合本身按依赖单例缓存，避免每次请求新建 partial 破坏下游缓存
    """
    return build_agent_tool_factories(
        spring_client, gozero_client, nestjs_client, vector_mapper, mcp_mapper
    )


AgentToolFactoriesDep = Annotated[
    AgentToolFactories, Depends(provide_agent_tool_factories)
]
