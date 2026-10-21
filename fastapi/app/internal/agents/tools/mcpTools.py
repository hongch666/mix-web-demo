import asyncio
import re
from typing import Any, Optional, cast

from langchain_core.tools import BaseTool, StructuredTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import Connection
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.base import Logger
from app.core.constants import Messages
from app.core.db import ASYNC_DATABASE_URL, AUTOCOMMIT
from app.internal.crud import McpServerConfigMapper, get_mcp_server_config_mapper
from app.internal.models import McpServerConfig

# MCP 工具名前缀，避免与内置 SQL/RAG 等工具重名
MCP_TOOL_NAME_PREFIX = "mcp_"
# 服务名清洗白名单之外的部分统一替换为下划线，保证拼出的工具名合法
MCP_SERVER_NAME_SANITIZE_PATTERN = re.compile(r"[^0-9a-zA-Z_]")


class MCPServerTools:
    """基于 mcp_server_config 表的 MCP 工具组

    连接粒度为每次调用建立短连接：工具发现与工具执行各自通过独立的
    MultiServerMCPClient 会话完成，避免长连接跨事件循环复用引发的
    绑定问题，同时让配置表变更无需重启即可生效
    """

    def __init__(self, mapper: Optional[McpServerConfigMapper] = None) -> None:
        """初始化 MCP 工具组并注入服务配置 Mapper，缺省取共享单例"""
        self._mapper: McpServerConfigMapper = mapper or get_mcp_server_config_mapper()

    def get_langchain_tools(self) -> list[StructuredTool]:
        """获取 LangChain MCP 工具对象列表

        工具装配在线程池工作线程中同步执行，线程内没有运行中的
        事件循环，用 asyncio.run 承载异步的配置读取与工具发现
        """
        return asyncio.run(self._load_tools_async())

    async def _load_tools_async(self) -> list[StructuredTool]:
        # 本方法运行在线程池的临时事件循环中，禁止使用共享的
        """用独立临时引擎读取启用的 MCP 服务配置并并发发现各服务的工具列表"""
        engine = create_async_engine(
            ASYNC_DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"autocommit": AUTOCOMMIT},
        )
        try:
            session_factory = async_sessionmaker(
                bind=engine, autoflush=False, expire_on_commit=False
            )
            async with session_factory() as db:
                configs: list[McpServerConfig] = await self._mapper.list_enabled_async(
                    db
                )
        finally:
            await engine.dispose()
        if not configs:
            Logger.info(Messages.MCP_NO_ENABLED_SERVERS())
            return []

        # 各服务独立发现工具并互相隔离，单个服务连接失败不影响其余服务
        results: list[Any] = await asyncio.gather(
            *(self._discover_server_tools(config) for config in configs),
            return_exceptions=True,
        )
        tools: list[StructuredTool] = []
        # gather 保序返回，configs 与 results 一一对应
        for config, result in zip(configs, results, strict=False):
            if isinstance(result, BaseException):
                # Column 标注的属性静态类型是 Column[T]，先按运行期值转为 str
                Logger.warning(
                    Messages.MCP_SERVER_LOAD_FAILED(str(config.server_name), result)
                )
            else:
                tools.extend(result)
        return tools

    async def _discover_server_tools(
        self, config: McpServerConfig
    ) -> list[StructuredTool]:
        """连接单个 MCP 服务发现工具并包装为 LangChain 工具"""
        # Column 标注的属性静态类型是 Column[T]，先读入运行期 str 局部变量
        server_name: str = str(config.server_name)
        server_key: str = self._sanitize_server_name(server_name)
        # langchain-mcp-adapters >= 0.3 已移除 async 上下文管理器，
        # 直接实例化后 get_tools：会话在每次工具调用时按需建立并关闭
        client = MultiServerMCPClient(self._build_connections(config, server_key))
        remote_tools: list[BaseTool] = await client.get_tools()

        tools: list[StructuredTool] = [
            self._wrap_remote_tool(config, remote_tool) for remote_tool in remote_tools
        ]
        Logger.info(Messages.MCP_SERVER_TOOLS_DISCOVERED(server_name, len(tools)))
        return tools

    def _wrap_remote_tool(
        self, config: McpServerConfig, remote_tool: BaseTool
    ) -> StructuredTool:
        """包装远程工具：工具名加服务前缀隔离，执行时按短连接调用"""
        # Column 标注的属性静态类型是 Column[T]，先读入运行期 str 局部变量
        server_name: str = str(config.server_name)
        description: str = str(remote_tool.description or config.description or "")

        async def run_tool(**kwargs: Any) -> Any:
            """包装远程 MCP 工具的执行闭包，调用时按短连接转发参数并执行"""
            return await self._invoke_remote_tool(config, remote_tool.name, kwargs)

        # args_schema 允许为空，仅在远程工具提供了 schema 时传入
        schema_extra: dict[str, Any] = (
            {"args_schema": remote_tool.args_schema}
            if remote_tool.args_schema is not None
            else {}
        )
        return StructuredTool(
            name=(
                f"{MCP_TOOL_NAME_PREFIX}"
                f"{self._sanitize_server_name(server_name)}_"
                f"{remote_tool.name}"
            ),
            description=description,
            coroutine=run_tool,
            **schema_extra,
        )

    async def _invoke_remote_tool(
        self, config: McpServerConfig, remote_tool_name: str, arguments: dict[str, Any]
    ) -> Any:
        """执行远程 MCP 工具，失败时返回可读错误文案供模型参考"""
        # Column 标注的属性静态类型是 Column[T]，先读入运行期 str 局部变量
        server_name: str = str(config.server_name)
        server_key: str = self._sanitize_server_name(server_name)
        try:
            # langchain-mcp-adapters >= 0.3 已移除 async 上下文管理器，
            # 直接实例化后 get_tools：会话在每次工具调用时按需建立并关闭
            client = MultiServerMCPClient(self._build_connections(config, server_key))
            remote_tools: list[BaseTool] = await client.get_tools()
            target: Optional[BaseTool] = next(
                (tool for tool in remote_tools if tool.name == remote_tool_name),
                None,
            )
            if target is None:
                Logger.warning(
                    Messages.MCP_TOOL_NOT_FOUND(server_name, remote_tool_name)
                )
                return Messages.MCP_TOOL_NOT_FOUND(server_name, remote_tool_name)
            return await target.ainvoke(arguments)
        except Exception as error:
            Logger.error(
                Messages.MCP_TOOL_EXECUTE_FAILED(server_name, remote_tool_name, error)
            )
            return Messages.MCP_TOOL_EXECUTE_FAILED(
                server_name, remote_tool_name, error
            )

    @staticmethod
    def _sanitize_server_name(server_name: str) -> str:
        """清洗服务名为合法工具名片段，供前缀隔离使用"""
        return MCP_SERVER_NAME_SANITIZE_PATTERN.sub("_", server_name)

    @staticmethod
    def _build_connections(
        config: McpServerConfig, server_key: str
    ) -> dict[str, Connection]:
        """构造适配器的单服务连接配置

        to_connection_config 按 transport_type 动态构造 dict[str, Any]，
        运行期结构与 Connection 联合类型兼容，这里统一收窄类型
        """
        return cast(
            dict[str, Connection],
            {server_key: config.to_connection_config()},
        )


def get_mcp_tools(
    mapper: Optional[McpServerConfigMapper] = None,
) -> MCPServerTools:
    """获取 MCP 工具组实例，每次装配重新读取配置表，保证变更即时生效"""
    return MCPServerTools(mapper)
