import redis
from typing import Optional, Any
import json
from config import load_config
from common.utils import fileLogger as logger


class RedisClient:
    """Redis 客户端 - 单例模式"""
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化 Redis 连接池"""
        try:
            redis_config = load_config("database")["redis"]
            
            # 创建连接池
            self._pool = redis.ConnectionPool(
                host=redis_config.get("host", "127.0.0.1"),
                port=redis_config.get("port", 6379),
                db=redis_config.get("db", 0),
                password=redis_config.get("password") or None,
                decode_responses=redis_config.get("decode_responses", True),
                max_connections=redis_config.get("max_connections", 10),
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            
            # 创建 Redis 客户端
            self._client = redis.Redis(connection_pool=self._pool)
            
            # 测试连接
            self._client.ping()
            logger.info(f"[Redis] 连接成功: {redis_config['host']}:{redis_config['port']}, DB: {redis_config['db']}")
            
        except Exception as e:
            logger.error(f"[Redis] 连接失败: {e}")
            self._client = None
    
    def get_client(self) -> Optional[redis.Redis]:
        """获取 Redis 客户端"""
        return self._client
    
    def is_available(self) -> bool:
        """检查 Redis 是否可用"""
        try:
            if self._client:
                self._client.ping()
                return True
        except:
            pass
        return False
    
    # ========== 基本操作 ==========
    
    def get(self, key: str) -> Optional[Any]:
        """获取值"""
        try:
            if not self._client:
                return None
            value = self._client.get(key)
            if value:
                # 尝试解析 JSON
                try:
                    return json.loads(value)
                except:
                    return value
            return None
        except Exception as e:
            logger.error(f"[Redis] GET 失败 key={key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """设置值
        
        Args:
            key: 键
            value: 值
            ex: 过期时间（秒）
        """
        try:
            if not self._client:
                return False
            
            # 序列化为 JSON
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            self._client.set(key, value, ex=ex)
            return True
        except Exception as e:
            logger.error(f"[Redis] SET 失败 key={key}: {e}")
            return False
    
    def delete(self, *keys: str) -> bool:
        """删除键"""
        try:
            if not self._client:
                return False
            self._client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"[Redis] DELETE 失败 keys={keys}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            if not self._client:
                return False
            return self._client.exists(key) > 0
        except Exception as e:
            logger.error(f"[Redis] EXISTS 失败 key={key}: {e}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        try:
            if not self._client:
                return False
            return self._client.expire(key, seconds)
        except Exception as e:
            logger.error(f"[Redis] EXPIRE 失败 key={key}: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """获取剩余生存时间（秒）
        
        Returns:
            -2: key 不存在
            -1: key 存在但未设置过期时间
            其他: 剩余秒数
        """
        try:
            if not self._client:
                return -2
            return self._client.ttl(key)
        except Exception as e:
            logger.error(f"[Redis] TTL 失败 key={key}: {e}")
            return -2
    
    def keys(self, pattern: str) -> list:
        """获取匹配的键列表"""
        try:
            if not self._client:
                return []
            return self._client.keys(pattern)
        except Exception as e:
            logger.error(f"[Redis] KEYS 失败 pattern={pattern}: {e}")
            return []
    
    def flushdb(self) -> bool:
        """清空当前数据库"""
        try:
            if not self._client:
                return False
            self._client.flushdb()
            logger.warning("[Redis] 数据库已清空")
            return True
        except Exception as e:
            logger.error(f"[Redis] FLUSHDB 失败: {e}")
            return False


# 全局单例
_redis_client = None

def get_redis_client() -> RedisClient:
    """获取 Redis 客户端单例"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client
