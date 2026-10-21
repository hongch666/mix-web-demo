from functools import partial
from typing import Annotated

from fastapi import Depends

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

from .clients import GozeroClientDep, NestjsClientDep, SpringClientDep
from .mappers import VectorMapperDep


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


def provide_mcp_tools() -> MCPServerTools:
    """装配 MCP 工具组工厂，工具实例在 initialize_ai_tools 中延迟构造

    构造与发现阶段读取 mcp_server_config 表，配置变更无需重启即可生效
    """
    return get_mcp_tools()


def provide_agent_tool_factories(
    spring_client: SpringClientDep,
    gozero_client: GozeroClientDep,
    nestjs_client: NestjsClientDep,
    vector_mapper: VectorMapperDep,
) -> AgentToolFactories:
    """装配 agent 工具组工厂集合

    只绑定已解析的客户端单例，工具实例延迟到 initialize_ai_tools 按组并行构造，
    从而保留单组失败隔离
    """
    return AgentToolFactories(
        sql_tools=(
            ("FastAPI", provide_fastapi_sql_tool),
            ("Spring", partial(provide_spring_sql_tool, spring_client)),
            ("GoZero", partial(provide_gozero_sql_tool, gozero_client)),
            ("NestJS", partial(provide_nestjs_sql_tool, nestjs_client)),
        ),
        rag=("RAG", partial(provide_rag_tools, vector_mapper)),
        neo4j=("Neo4j 知识图谱", provide_neo4j_tools),
        mongodb=("MongoDB 日志", partial(provide_mongodb_tools, nestjs_client)),
        warehouse=("ClickHouse 数仓", provide_warehouse_tools),
        mcp_servers=(("MCP 服务", provide_mcp_tools),),
    )


AgentToolFactoriesDep = Annotated[
    AgentToolFactories, Depends(provide_agent_tool_factories)
]
