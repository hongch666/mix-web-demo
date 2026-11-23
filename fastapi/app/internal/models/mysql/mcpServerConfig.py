from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class McpServerConfig(Base):
    """Agent MCP 服务配置实体类"""

    __tablename__ = "mcp_server_config"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    # MCP 服务名，同时作为工具名前缀用于跨服务隔离
    server_name: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    # 传输类型: stdio / sse / streamable_http
    transport_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # stdio 传输的可执行命令与参数数组，其余传输为空
    command: Mapped[str | None] = mapped_column(String(255), nullable=True)
    args_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    # sse / streamable_http 传输的服务地址，stdio 传输为空
    url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # stdio 传输的环境变量与 HTTP 传输的请求头，敏感凭证加密后落库
    env_json: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True)
    headers_json: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    # 1 启用，0 停用，停用后 Agent 不加载该服务的工具
    enabled: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=datetime.now
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=datetime.now
    )

    def to_connection_config(self) -> dict[str, Any]:
        """转换为 langchain-mcp-adapters 的单服务连接配置"""
        transport = self.transport_type
        command = self.command
        args_json = self.args_json
        env_json = self.env_json
        url = self.url
        headers_json = self.headers_json

        if transport == "stdio":
            config: dict[str, Any] = {
                "transport": "stdio",
                "command": command or "",
                "args": list(args_json or []),
            }
            if env_json:
                config["env"] = dict(env_json)
            return config

        config = {
            "transport": transport,
            "url": url or "",
        }
        if headers_json:
            config["headers"] = dict(headers_json)
        return config
