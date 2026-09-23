from functools import lru_cache
from typing import Any, Optional
from urllib.parse import quote

from neomodel import adb

from app.core.base import Logger
from app.core.config import load_config
from app.core.constants import Messages


class Neo4jClient:
    """基于 neomodel 的 Neo4j 异步客户端

    连接的创建、持有与关闭全部交给 neomodel 的全局 AsyncDatabase（adb），
    整个进程只维护一条连接（驱动 + 连接池），OGM 对象操作与原始 Cypher
    共用同一连接，不再各自建立驱动
    """

    def __init__(self) -> None:
        self.logger = Logger
        self.uri: str = ""
        self.user: str = ""
        self.password: str = ""
        self._initialize_config()

    def _initialize_config(self) -> None:
        """根据配置初始化 Neo4j 连接参数"""
        try:
            neo4j_cfg: dict[str, Any] = (load_config("database") or {}).get(
                "neo4j"
            ) or {}
            self.uri = str(neo4j_cfg["uri"]).strip()
            self.user = str(neo4j_cfg["user"]).strip()
            self.password = str(neo4j_cfg["password"]).strip()
            self.logger.info(Messages.NEO4J_CONFIG_INITIALIZED(self.uri))
        except Exception as e:
            self.uri = ""
            self.logger.error(Messages.NEO4J_CONFIG_INITIALIZATION_FAILED(e))

    def _build_connection_url(self) -> str:
        """拼装 neomodel 所需的连接 URL（账号密码做 URL 编码）

        neomodel 要求 URL 形如 ``protocol://user:password@host:port``，即使密码为空
        也要保留分隔用的冒号
        """
        scheme, separator, host = self.uri.partition("://")
        if not separator or not scheme or not host:
            return self.uri
        username: str = quote(self.user, safe="")
        password: str = quote(self.password, safe="")
        return f"{scheme}://{username}:{password}@{host}"

    async def connect(self) -> bool:
        """建立 neomodel 连接（幂等），全进程复用同一条连接"""
        if adb.driver is not None:
            return True

        if not self.uri:
            self.logger.warning(Messages.NEO4J_CONFIG_NOT_INITIALIZED_MESSAGE)
            return False

        try:
            # 驱动创建、连接池、事务管理全部交给 neomodel
            await adb.set_connection(url=self._build_connection_url())
            self.logger.info(Messages.NEO4J_DRIVER_INITIALIZED(self.uri))
            return True
        except Exception as e:
            self.logger.error(Messages.NEO4J_CONNECTION_FAILED(e))
            return False

    async def run_query(
        self, cypher: str, params: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        """执行只读 Cypher 查询，返回字典列表"""
        if not await self.connect():
            return []

        try:
            # neomodel 的 cypher_query 返回 (行值列表, 列名元组)，这里还原为字典列表
            records: list[Any]
            columns: Any
            records, columns = await adb.cypher_query(cypher, params or {})
            headers: list[str] = list(columns)
            return [dict(zip(headers, row, strict=False)) for row in records]
        except Exception as e:
            self.logger.error(Messages.CYPHER_QUERY_FAILED(e, cypher, params))
            return []

    async def run_write_query(
        self, cypher: str, params: Optional[dict[str, Any]] = None
    ) -> Optional[Any]:
        """执行写入类 Cypher 语句，返回查询摘要（含删除计数）

        写入需要 Neo4j 的 counters 摘要，而 neomodel 的 cypher_query 不返回摘要，
        故复用 neomodel 持有的同一个驱动执行，不额外建立连接
        """
        if not await self.connect():
            return None

        driver: Any = adb.driver
        if driver is None:
            self.logger.warning(Messages.NEO4J_DRIVER_NOT_INITIALIZED_MESSAGE)
            return None

        try:
            async with driver.session() as session:
                result: Any = await session.run(cypher, params or {})
                return await result.consume()
        except Exception as e:
            self.logger.error(Messages.CYPHER_WRITE_FAILED(e, cypher, params))
            return None

    async def close(self) -> None:
        """关闭 neomodel 持有的连接"""
        try:
            await adb.close_connection()
            self.logger.info(Messages.NEO4J_DRIVER_CLOSED_MESSAGE)
        except Exception as e:
            self.logger.error(Messages.NEO4J_CONNECTION_CLOSE_FAILED(e))


@lru_cache
def get_neo4j_client() -> Neo4jClient:
    """获取 Neo4j 客户端单例"""
    return Neo4jClient()
