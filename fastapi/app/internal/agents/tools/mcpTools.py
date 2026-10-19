import asyncio
import re
from typing import Any, Optional

from langchain_core.tools import BaseTool, StructuredTool

from app.core.base import Logger
from app.core.constants import Messages
from app.core.db import AsyncSessionLocal
from app.internal.crud import McpServerConfigMapper, get_mcp_server_config_mapper
from app.internal.models import McpServerConfig

# MCP 适配器为可选依赖，未安装时该工具组降级为空且不影响其他工具组
try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
except ImportError:  # pragma: no cover
    MultiServerMCPClient = None  # type: ignore[assignment]

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
        self._mapper: McpServerConfigMapper = mapper or get_mcp_server_config_mapper()

    def get_langchain_tools(self) -> list[StructuredTool]:
        """获取 LangChain MCP 工具对象列表

        工具装配在线程池工作线程中同步执行，线程内没有运行中的
        事件循环，用 asyncio.run 承载异步的配置读取与工具发现
        """
        return asyncio.run(self._load_tools_async())

    async def _load_tools_async(self) -> list[StructuredTool]:
        if MultiServerMCPClient is None:
            Logger.warning(Messages.MCP_ADAPTER_NOT_INSTALLED())
            return []

        async with AsyncSessionLocal() as db:
            configs: list[McpServerConfig] = await self._mapper.list_enabled_async(db)
        if not configs:
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
                Logger.warning(
                    Messages.MCP_SERVER_LOAD_FAILED(config.server_name, result)
                )
            else:
                tools.extend(result)
        return tools

    async def _discover_server_tools(
        self, config: McpServerConfig
    ) -> list[StructuredTool]:
        """连接单个 MCP 服务发现工具并包装为 LangChain 工具"""
        server_key: str = self._sanitize_server_name(config.server_name)
        connection_config: dict[str, dict[str, Any]] = {
            server_key: config.to_connection_config()
        }
        async with MultiServerMCPClient(connection_config) as client:
            remote_tools: list[BaseTool] = await client.get_tools()

        tools: list[StructuredTool] = [
            self._wrap_remote_tool(config, remote_tool) for remote_tool in remote_tools
        ]
        Logger.info(
            Messages.MCP_SERVER_TOOLS_DISCOVERED(config.server_name, len(tools))
        )
        return tools

    def _wrap_remote_tool(
        self, config: McpServerConfig, remote_tool: BaseTool
    ) -> StructuredTool:
        """包装远程工具：工具名加服务前缀隔离，执行时按短连接调用"""

        async def run_tool(**kwargs: Any) -> Any:
            return await self._invoke_remote_tool(config, remote_tool.name, kwargs)

        return StructuredTool(
            name=(
                f"{MCP_TOOL_NAME_PREFIX}"
                f"{self._sanitize_server_name(config.server_name)}_"
                f"{remote_tool.name}"
            ),
            description=remote_tool.description or config.description,
            coroutine=run_tool,
            args_schema=remote_tool.args_schema,
        )

    async def _invoke_remote_tool(
        self, config: McpServerConfig, remote_tool_name: str, arguments: dict[str, Any]
    ) -> Any:
        """执行远程 MCP 工具，失败时返回可读错误文案供模型参考"""
        server_key: str = self._sanitize_server_name(config.server_name)
        try:
            async with MultiServerMCPClient(
                {server_key: config.to_connection_config()}
            ) as client:
                remote_tools: list[BaseTool] = await client.get_tools()
                target: Optional[BaseTool] = next(
                    (tool for tool in remote_tools if tool.name == remote_tool_name),
                    None,
                )
                if target is None:
                    Logger.warning(
                        Messages.MCP_TOOL_NOT_FOUND(
                            config.server_name, remote_tool_name
                        )
                    )
                    return Messages.MCP_TOOL_NOT_FOUND(
                        config.server_name, remote_tool_name
                    )
                return await target.ainvoke(arguments)
        except Exception as error:
            Logger.error(
                Messages.MCP_TOOL_EXECUTE_FAILED(
                    config.server_name, remote_tool_name, error
                )
            )
            return Messages.MCP_TOOL_EXECUTE_FAILED(
                config.server_name, remote_tool_name, error
            )

    @staticmethod
    def _sanitize_server_name(server_name: str) -> str:
        """清洗服务名为合法工具名片段，供前缀隔离使用"""
        return MCP_SERVER_NAME_SANITIZE_PATTERN.sub("_", server_name)


def get_mcp_tools(
    mapper: Optional[McpServerConfigMapper] = None,
) -> MCPServerTools:
    """获取 MCP 工具组实例，每次装配重新读取配置表，保证变更即时生效"""
    return MCPServerTools(mapper)
