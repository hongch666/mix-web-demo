from functools import lru_cache

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.internal.models import McpServerConfig


class McpServerConfigMapper:
    """Agent MCP 服务配置 Mapper"""

    async def list_enabled_async(self, db: AsyncSession) -> list[McpServerConfig]:
        """查询启用中的 MCP 服务配置，按名称排序保证装配顺序稳定"""
        statement = (
            select(McpServerConfig)
            .where(McpServerConfig.enabled == 1)
            .order_by(McpServerConfig.server_name.asc())
        )
        return list((await db.execute(statement)).scalars().all())


@lru_cache
def get_mcp_server_config_mapper() -> McpServerConfigMapper:
    """获取 MCP 服务配置 Mapper 的进程级单例"""
    return McpServerConfigMapper()
