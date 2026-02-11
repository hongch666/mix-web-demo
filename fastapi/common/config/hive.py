import time
from pyhive import hive
from common.config import load_config
from common.utils import fileLogger as logger, Constants

class HiveConnectionPool:
    """Hive 连接池 - 单例模式"""
    
    _instance = None
    _connections = []
    _max_connections = 10
    _conn_count = 0  # 统计创建的连接数
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_connection(self):
        """从池中获取连接"""
        if self._connections:
            logger.info(f"[连接池] 从池中获取复用连接，池内剩余: {len(self._connections) - 1}个")
            return self._connections.pop()
        
        # 如果池为空，创建新连接
        hive_config = load_config("database")["hive"]
        hive_host = hive_config["host"]
        hive_port = hive_config["port"]
        hive_db = hive_config["database"]
        hive_username = hive_config.get("username")
        hive_password = hive_config.get("password")
        
        self._conn_count += 1
        logger.info(f"[连接池] 创建新 Hive 连接 (第{self._conn_count}个)")
        conn_start = time.time()
        
        # 根据是否有账号密码来构建连接
        conn_params = {
            "host": hive_host,
            "port": hive_port,
            "database": hive_db
        }
        
        if hive_username:
            conn_params["username"] = hive_username
        if hive_password:
            conn_params["password"] = hive_password
        
        conn = hive.Connection(**conn_params)
        conn_time = time.time() - conn_start
        logger.info(f"[连接池] Hive 连接建立耗时 {conn_time:.3f}s")
        return conn
    
    def return_connection(self, conn):
        """归还连接到池"""
        if len(self._connections) < self._max_connections:
            self._connections.append(conn)
            logger.info(f"[连接池] 连接已归还到池，池内现有: {len(self._connections)}个")
        else:
            conn.close()
            logger.info(Constants.HIVE_CONNECTION_POOL_FULL_MESSAGE)


# 全局单例
_hive_pool = None

def get_hive_connection_pool() -> HiveConnectionPool:
    """获取 Hive 连接池单例"""
    global _hive_pool
    if _hive_pool is None:
        _hive_pool = HiveConnectionPool()
    return _hive_pool
