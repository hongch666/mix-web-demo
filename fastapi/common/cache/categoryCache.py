import time
import hashlib
from typing import Optional, List, Dict, Any
from functools import lru_cache
from config.redis import get_redis_client
from common.utils import fileLogger as logger

# 全局单例实例
_category_cache_instance = None


class CategoryCache:
    """
    分类文章数缓存管理 - 二级缓存架构
    
    缓存策略：
    1. L1 缓存（本地内存）- 10分钟 TTL
    2. L2 缓存（Redis）- 1天 TTL
    3. 版本号检测 - Hive 表变化时自动失效
    """
    
    # Redis 键前缀
    REDIS_KEY_PREFIX = "category:article_count"
    REDIS_VERSION_KEY = "category:article_count:version"
    
    def __init__(self):
        # L1 本地缓存
        self._local_cache = None
        self._local_cache_time = 0
        self._local_cache_ttl = 300  # 5分钟
        
        # 版本号
        self._cache_version = None
        
        # Redis 客户端
        self._redis = get_redis_client()
        
        # Redis TTL（1天）
        self._redis_ttl = 86400
    
    def __repr__(self) -> str:
        """对象表示 - 用于日志输出和序列化"""
        return "CategoryCache()"
    
    def __str__(self) -> str:
        """字符串表示"""
        return "CategoryCache()"
    
    def get_cache_version(self, hive_conn) -> Optional[str]:
        """获取 Hive articles 表的版本号"""
        try:
            with hive_conn.cursor() as cursor:
                cursor.execute("SHOW TBLPROPERTIES articles")
                props = cursor.fetchall()
                version_str = str(props)
                return hashlib.md5(version_str.encode()).hexdigest()[:8]
        except Exception as e:
            logger.warning(f"获取表版本号失败: {e}")
            return None
    
    def is_local_cache_valid(self) -> bool:
        """检查本地缓存是否有效"""
        if not self._local_cache:
            return False
        
        # 检查 TTL
        if time.time() - self._local_cache_time > self._local_cache_ttl:
            logger.info("[L1缓存-分类] TTL过期")
            return False
        
        return True
    
    def get_from_local(self) -> Optional[List[Dict[str, Any]]]:
        """从本地缓存获取"""
        if self.is_local_cache_valid():
            cache_age = time.time() - self._local_cache_time
            logger.info(f"[L1缓存-分类] 命中，缓存年龄: {cache_age:.1f}s")
            return self._local_cache
        return None
    
    def get_from_redis(self) -> Optional[List[Dict[str, Any]]]:
        """从 Redis 缓存获取"""
        try:
            if not self._redis.is_available():
                logger.warning("[L2缓存-分类] Redis 不可用")
                return None
            
            data = self._redis.get(self.REDIS_KEY_PREFIX)
            if data:
                logger.info("[L2缓存-分类] 命中 Redis")
                # 同时更新本地缓存
                self._local_cache = data
                self._local_cache_time = time.time()
                return data
            
            logger.info("[L2缓存-分类] Redis 未命中")
            return None
        except Exception as e:
            logger.error(f"[L2缓存-分类] Redis 读取失败: {e}")
            return None
    
    def is_version_changed(self, hive_conn) -> bool:
        """检查版本号是否变化"""
        try:
            current_version = self.get_cache_version(hive_conn)
            if not current_version:
                return False
            
            # 从 Redis 获取旧版本号
            old_version = None
            if self._redis.is_available():
                old_version = self._redis.get(self.REDIS_VERSION_KEY)
            
            # 本地也有版本号
            if not old_version:
                old_version = self._cache_version
            
            if old_version and current_version != old_version:
                logger.info(f"[缓存-分类] 表版本已变化 (旧: {old_version} → 新: {current_version})")
                return True
            
            return False
        except Exception as e:
            logger.warning(f"版本检测异常: {e}")
            return False
    
    def get(self, hive_conn) -> Optional[List[Dict[str, Any]]]:
        """
        获取缓存（二级缓存）
        
        查找顺序：
        1. 本地内存缓存（L1）
        2. Redis 缓存（L2）
        3. 返回 None（需要查询 Hive）
        """
        # 检查版本号是否变化
        if self.is_version_changed(hive_conn):
            logger.info("[缓存-分类] 版本变化，清除所有缓存")
            self.clear_all()
            return None
        
        # 1. 先查本地缓存
        local_data = self.get_from_local()
        if local_data:
            return local_data
        
        # 2. 本地缓存失效，查 Redis
        redis_data = self.get_from_redis()
        if redis_data:
            return redis_data
        
        # 3. 两级缓存都没有
        logger.info("[缓存-分类] L1/L2 都未命中，需要查询 Hive")
        return None
    
    def set(self, data: List[Dict[str, Any]], hive_conn):
        """
        设置缓存（二级缓存）
        
        同时更新：
        1. 本地内存缓存（L1）
        2. Redis 缓存（L2）
        3. 版本号
        """
        # 1. 更新本地缓存
        self._local_cache = data
        self._local_cache_time = time.time()
        logger.info("[L1缓存-分类] 已更新")
        
        # 2. 更新 Redis 缓存
        try:
            if self._redis.is_available():
                self._redis.set(self.REDIS_KEY_PREFIX, data, ex=self._redis_ttl)
                logger.info(f"[L2缓存-分类] 已更新 Redis，TTL={self._redis_ttl}s (1天)")
        except Exception as e:
            logger.error(f"[L2缓存-分类] Redis 写入失败: {e}")
        
        # 3. 更新版本号
        try:
            version = self.get_cache_version(hive_conn)
            if version:
                self._cache_version = version
                if self._redis.is_available():
                    self._redis.set(self.REDIS_VERSION_KEY, version, ex=self._redis_ttl)
                logger.info(f"[缓存-分类] 版本号已更新: {version}")
        except Exception as e:
            logger.warning(f"设置缓存版本号失败: {e}")
    
    def clear_all(self):
        """清除所有缓存"""
        # 清除本地缓存
        self._local_cache = None
        self._local_cache_time = 0
        self._cache_version = None
        logger.info("[L1缓存-分类] 已清除")
        
        # 清除 Redis 缓存
        try:
            if self._redis.is_available():
                self._redis.delete(self.REDIS_KEY_PREFIX, self.REDIS_VERSION_KEY)
                logger.info("[L2缓存-分类] Redis 已清除")
        except Exception as e:
            logger.error(f"[L2缓存-分类] Redis 清除失败: {e}")

@lru_cache()
def get_category_cache() -> CategoryCache:
    """获取 CategoryCache 单例实例"""
    global _category_cache_instance
    if _category_cache_instance is None:
        _category_cache_instance = CategoryCache()
    return _category_cache_instance
