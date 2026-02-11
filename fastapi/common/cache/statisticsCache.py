import time
from typing import Optional, Dict, Any
from functools import lru_cache
from common.config import get_redis_client
from common.utils import fileLogger as logger, Constants

# 全局单例实例
_statistics_cache_instance = None

class StatisticsCache:
    """
    文章统计信息缓存 - 二级缓存架构
    
    缓存策略：
    1. L1 缓存（本地内存）- 10分钟 TTL
    2. L2 缓存（Redis）- 1天 TTL
    3. 版本号检测 - MySQL 表变化时自动失效
    """
    
    # Redis 键前缀
    REDIS_KEY_PREFIX = "article:statistics"
    REDIS_VERSION_KEY = "article:statistics:version"
    
    def __init__(self):
        # L1 本地缓存
        self._local_cache = None
        self._local_cache_time = 0
        self._local_cache_ttl = 600  # 10分钟
        
        # 版本号
        self._cache_version = None
        
        # Redis 客户端
        self._redis = get_redis_client()
        
        # Redis TTL（1天）
        self._redis_ttl = 86400
    
    def __repr__(self) -> str:
        """对象表示 - 用于日志输出和序列化"""
        return "StatisticsCache()"
    
    def __str__(self) -> str:
        """字符串表示"""
        return "StatisticsCache()"
    
    def is_local_cache_valid(self) -> bool:
        """检查本地缓存是否有效"""
        if not self._local_cache:
            return False
        
        # 检查 TTL
        if time.time() - self._local_cache_time > self._local_cache_ttl:
            logger.info(Constants.L1_CACHE_TTL_EXPIRED)
            return False
        
        return True
    
    def get_from_local(self) -> Optional[Dict[str, Any]]:
        """从本地缓存获取"""
        if self.is_local_cache_valid():
            cache_age = time.time() - self._local_cache_time
            logger.info(f"[L1缓存] 命中，缓存年龄: {cache_age:.1f}s")
            return self._local_cache
        return None
    
    def get_from_redis(self) -> Optional[Dict[str, Any]]:
        """从 Redis 缓存获取"""
        try:
            if not self._redis.is_available():
                logger.warning(Constants.L2_CACHE_UNAVAILABLE)
                return None
            
            data = self._redis.get(self.REDIS_KEY_PREFIX)
            if data:
                logger.info(Constants.L2_CACHE_HIT)
                # 同时更新本地缓存
                self._local_cache = data
                self._local_cache_time = time.time()
                return data
            
            logger.info(Constants.L2_CACHE_MISS)
            return None
        except Exception as e:
            logger.error(f"[L2缓存] Redis 读取失败: {e}")
            return None
    
    def get(self) -> Optional[Dict[str, Any]]:
        """
        获取缓存（二级缓存）
        
        查找顺序：
        1. 本地内存缓存（L1）
        2. Redis 缓存（L2）
        3. 返回 None（需要查询 DB）
        """
        # 1. 先查本地缓存
        local_data = self.get_from_local()
        if local_data:
            return local_data
        
        # 2. 本地缓存失效，查 Redis
        redis_data = self.get_from_redis()
        if redis_data:
            return redis_data
        
        # 3. 两级缓存都没有
        logger.info(Constants.DB_CACHE_MISS_QUERY_DB_MESSAGE)
        return None
    
    def set(self, data: Dict[str, Any]):
        """
        设置缓存（二级缓存）
        
        同时更新：
        1. 本地内存缓存（L1）
        2. Redis 缓存（L2）
        """
        # 1. 更新本地缓存
        self._local_cache = data
        self._local_cache_time = time.time()
        logger.info(Constants.L1_CACHE_UPDATED)
        
        # 2. 更新 Redis 缓存
        try:
            if self._redis.is_available():
                self._redis.set(self.REDIS_KEY_PREFIX, data, ex=self._redis_ttl)
                logger.info(f"[L2缓存] 已更新 Redis，TTL={self._redis_ttl}s (1天)")
        except Exception as e:
            logger.error(f"[L2缓存] Redis 写入失败: {e}")
    
    def clear_all(self):
        """清除所有缓存"""
        # 清除本地缓存
        self._local_cache = None
        self._local_cache_time = 0
        self._cache_version = None
        logger.info("[L1缓存] 已清除")
        
        # 清除 Redis 缓存
        try:
            if self._redis.is_available():
                self._redis.delete(self.REDIS_KEY_PREFIX, self.REDIS_VERSION_KEY)
                logger.info(Constants.L2_CACHE_CLEARED)
        except Exception as e:
            logger.error(f"[L2缓存] Redis 清除失败: {e}")


@lru_cache()
def get_statistics_cache() -> StatisticsCache:
    """获取 StatisticsCache 单例实例"""
    global _statistics_cache_instance
    if _statistics_cache_instance is None:
        _statistics_cache_instance = StatisticsCache()
    return _statistics_cache_instance
