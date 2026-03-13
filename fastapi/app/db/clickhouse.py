import time
from typing import Any, List, Optional

from clickhouse_driver import Client

from app.core import Constants, Logger, load_config


class ClickhouseConnectionPool:
    """ClickHouse 连接池 - 单例模式"""

    _instance: Optional["ClickhouseConnectionPool"] = None
    _connections: List[Any] = []
    _max_connections: int = 10
    _conn_count: int = 0  # 统计创建的连接数

    def __new__(cls) -> "ClickhouseConnectionPool":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_connection(self) -> Any:
        """从池中获取连接"""
        if self._connections:
            Logger.info(
                f"[ClickHouse连接池] 从池中获取复用连接，池内剩余: {len(self._connections) - 1}个"
            )
            return self._connections.pop()

        # 如果池为空，创建新连接
        clickhouse_config = load_config("database")["clickhouse"]
        ch_host = str(clickhouse_config["host"])
        ch_port = int(clickhouse_config["port"])
        ch_database = str(clickhouse_config["database"])
        ch_username = str(clickhouse_config.get("username", "default"))
        # 确保密码始终是字符串类型
        ch_password = str(clickhouse_config.get("password", ""))
        if ch_password and ch_password.isdigit():
            # 如果密码全是数字，保持原样；如果是 "0" 或其他特殊值则转为空
            pass
        elif not ch_password or ch_password == "None":
            ch_password = ""

        self._conn_count += 1
        Logger.info(f"[ClickHouse连接池] 创建新连接 (第{self._conn_count}个)")
        Logger.info(
            f"[ClickHouse连接池] 连接配置 - Host: {ch_host}, Port: {ch_port}, DB: {ch_database}, User: {ch_username}"
        )
        conn_start = time.time()

        try:
            conn = Client(
                host=ch_host,
                port=ch_port,
                database=ch_database,
                user=ch_username,
                password=ch_password,
                settings={"use_numpy": False},
                client_name="fastapi-app",
            )
            conn_time = time.time() - conn_start
            Logger.info(f"[ClickHouse连接池] 连接建立耗时 {conn_time:.3f}s")
            return conn
        except Exception as e:
            Logger.error(f"[ClickHouse连接池] 创建连接失败: {e}")
            raise

    def return_connection(self, conn: Any) -> None:
        """归还连接到池"""
        if len(self._connections) < self._max_connections:
            self._connections.append(conn)
            Logger.info(
                f"[ClickHouse连接池] 连接已归还到池，池内现有: {len(self._connections)}个"
            )
        else:
            try:
                conn.disconnect()
            except Exception:
                pass
            Logger.info(Constants.CLICKHOUSE_CONNECTION_POOL_FULL_MESSAGE)

    def close_all(self) -> None:
        """关闭所有连接"""
        for conn in self._connections:
            try:
                conn.disconnect()
            except Exception:
                pass
        self._connections.clear()
        Logger.info(Constants.CLICKHOUSE_CONNECTION_POOL_CLOSED_MESSAGE)


# 全局单例
_clickhouse_pool: Optional[ClickhouseConnectionPool] = None


def get_clickhouse_connection_pool() -> ClickhouseConnectionPool:
    """获取ClickHouse连接池单例"""
    global _clickhouse_pool
    if _clickhouse_pool is None:
        _clickhouse_pool = ClickhouseConnectionPool()
    return _clickhouse_pool
