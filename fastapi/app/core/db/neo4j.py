import io
import logging
from functools import lru_cache
from typing import Any, Optional
from urllib.parse import quote

from neomodel import adb
from neomodel.config import get_config

from app.core.base import Logger
from app.core.config import load_config
from app.core.constants import Messages

# neomodel 输出 Cypher 调试日志所用的 logger，异步与同步实现各持有一个
NEO4J_QUERY_LOGGER_NAMES: tuple[str, ...] = (
    "neomodel.async_.query",
    "neomodel.sync_.query",
)


class CypherDebugLogHandler(logging.Handler):
    """把 neomodel 生成的 Cypher 调试日志转交项目日志封装

    neomodel 只调用 logger.debug 且自身不注册 handler，root 默认也没有 handler，
    DEBUG 记录会被 logging 直接丢弃，因此开启开关时必须由应用侧接管输出
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            Logger.debug(record.getMessage())
        except Exception:
            self.handleError(record)


def resolve_cypher_debug_config(
    neo4j_config: Optional[dict[str, Any]],
) -> tuple[bool, float]:
    """解析 Cypher 调试开关与慢查询阈值

    配置段缺失、开关未声明或取值无法识别为真时关闭调试；
    慢查询阈值非法时回落到 0 秒（neomodel 视为不设下限）
    """
    if not isinstance(neo4j_config, dict):
        return False, 0.0

    raw_enabled: Any = neo4j_config.get("cypher_debug")
    if isinstance(raw_enabled, bool):
        enabled: bool = raw_enabled
    elif isinstance(raw_enabled, str):
        enabled = raw_enabled.strip().lower() in {"true", "1", "yes", "on"}
    else:
        enabled = bool(raw_enabled)

    raw_threshold: Any = neo4j_config.get("slow_queries", 0.0)
    try:
        slow_queries: float = max(0.0, float(raw_threshold))
    except (TypeError, ValueError):
        slow_queries = 0.0

    return enabled, slow_queries


def apply_cypher_debug_config(enabled: bool, slow_queries: float = 0.0) -> None:
    """把 Cypher 调试开关同步到 neomodel 并接管其日志输出

    neomodel 会自行从标准进程环境读取 NEOMODEL_CYPHER_DEBUG 与
    NEOMODEL_SLOW_QUERIES，这里以项目 YAML 配置为准显式覆盖，保证配置来源唯一
    """
    settings = get_config()
    settings.cypher_debug = enabled
    settings.slow_queries = slow_queries

    for name in NEO4J_QUERY_LOGGER_NAMES:
        query_logger: logging.Logger = logging.getLogger(name)
        # 重复应用时先摘掉旧 handler，避免同一条日志被输出多次
        query_logger.handlers = [
            handler
            for handler in query_logger.handlers
            if not isinstance(handler, CypherDebugLogHandler)
        ]
        query_logger.setLevel(logging.DEBUG if enabled else logging.NOTSET)
        # 项目已接管输出，关闭向上传播，避免 root 配置了 handler 时重复打印
        query_logger.propagate = not enabled
        if enabled:
            query_logger.addHandler(CypherDebugLogHandler())


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
        self._schema_installed: bool = False
        self._initialize_config()

    def _initialize_config(self) -> None:
        """根据配置初始化 Neo4j 连接参数并接管 Cypher 调试日志"""
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
            return

        cypher_debug, slow_queries = resolve_cypher_debug_config(neo4j_cfg)
        try:
            apply_cypher_debug_config(cypher_debug, slow_queries)
        except Exception as e:
            self.logger.error(Messages.NEO4J_CYPHER_DEBUG_CONFIG_FAILED(e))
            return

        if cypher_debug:
            self.logger.info(Messages.NEO4J_CYPHER_DEBUG_ENABLED(slow_queries))

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

    async def install_schema(self) -> None:
        """按 neomodel 模型声明安装图谱约束与索引

        neomodel 通过 AsyncStructuredNode 的子类发现模型，故先延迟导入
        app.internal.models 触发节点类注册（与 ClickHouse 建表同样处理，
        避免 app.core.db 与 app.internal.models 循环依赖）

        安装动作本身不带 IF NOT EXISTS，重复执行只会触发等价约束已存在
        的异常，因此全进程只安装一次
        """
        if self._schema_installed:
            return

        # 延迟导入触发节点类注册，neomodel 按已注册子类的唯一索引声明建约束
        from app.internal.models import (  # noqa: F401
            Article,
            Category,
            SubCategory,
            Tag,
            User,
        )

        if not await self.connect():
            return

        # neomodel 会把每个类的安装明细写入 stdout，这里转交项目日志
        buffer = io.StringIO()
        try:
            await adb.install_all_labels(stdout=buffer)
        except Exception as e:
            self.logger.error(Messages.NEO4J_SCHEMA_INSTALL_FAILED(e))
            return

        self._schema_installed = True
        self.logger.info(Messages.NEO4J_SCHEMA_INSTALLED_MESSAGE)
        detail = buffer.getvalue().strip()
        if detail:
            self.logger.debug(detail)

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
