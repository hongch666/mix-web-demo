import asyncio
from functools import lru_cache
from typing import Any, Dict, List, Optional

from app.core.base import Logger
from app.core.config import load_config
from neo4j import AsyncGraphDatabase, AsyncSession


class Neo4jClient:
    """Neo4j 异步客户端封装"""

    def __init__(self) -> None:
        self.logger = Logger
        self.uri: str = ""
        self.user: str = ""
        self.password: str = ""
        self.auth: Optional[tuple[str, str]] = None
        self._drivers: Dict[int, Any] = {}
        self._initialize_config()

    def _initialize_config(self) -> None:
        """根据配置初始化 Neo4j 连接参数"""
        try:
            neo4j_cfg = load_config("neo4j") or {}
            self.uri = str(neo4j_cfg.get("uri") or "bolt://127.0.0.1:7687")
            self.user = str(neo4j_cfg.get("user") or "neo4j")
            self.password = str(neo4j_cfg.get("password") or "").strip()
            self.auth = (self.user, self.password) if self.password else None
            self.logger.info(f"Neo4j 连接参数初始化成功: {self.uri}")
        except Exception as e:
            self.uri = ""
            self.auth = None
            self.logger.error(f"Neo4j 连接参数初始化失败: {e}")

    def _get_driver(self) -> Optional[Any]:
        """获取当前事件循环对应的 Neo4j 驱动"""
        if not self.uri:
            self.logger.warning("Neo4j 连接参数未初始化，无法创建驱动")
            return None

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            self.logger.warning("当前没有运行中的事件循环，无法创建 Neo4j 异步驱动")
            return None

        loop_id = id(loop)
        driver = self._drivers.get(loop_id)
        if driver is None:
            driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=self.auth,
                max_connection_lifetime=3600,
            )
            self._drivers[loop_id] = driver
            self.logger.info(f"Neo4j 驱动初始化成功: {self.uri}")
        return driver

    async def get_session(self) -> Optional[AsyncSession]:
        """获取 Neo4j 异步会话"""
        driver = self._get_driver()
        if driver is None:
            self.logger.warning("Neo4j 驱动未初始化，无法创建会话")
            return None
        return driver.session()

    async def run_query(
        self, cypher: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """执行只读 Cypher 查询"""
        session = await self.get_session()
        if session is None:
            return []

        try:
            result = await session.run(cypher, params or {})
            return await result.data()
        except Exception as e:
            self.logger.error(f"Cypher 查询失败: {e}\nCypher: {cypher}\nParams: {params}")
            return []
        finally:
            await session.close()

    async def run_write_query(
        self, cypher: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """执行写入类 Cypher 语句"""
        session = await self.get_session()
        if session is None:
            return None

        try:
            result = await session.run(cypher, params or {})
            return await result.consume()
        except Exception as e:
            self.logger.error(f"Cypher 写操作失败: {e}\nCypher: {cypher}\nParams: {params}")
            return None
        finally:
            await session.close()

    async def close(self) -> None:
        """关闭 Neo4j 驱动连接"""
        try:
            current_loop_id = id(asyncio.get_running_loop())
        except RuntimeError:
            current_loop_id = None

        if current_loop_id is not None:
            driver = self._drivers.pop(current_loop_id, None)
            if driver is not None:
                await driver.close()
                self.logger.info("Neo4j 当前事件循环驱动已关闭")
            return

        for driver in list(self._drivers.values()):
            await driver.close()
        self._drivers.clear()
        self.logger.info("Neo4j 驱动已关闭")


@lru_cache
def get_neo4j_client() -> Neo4jClient:
    """获取 Neo4j 客户端单例"""
    return Neo4jClient()
