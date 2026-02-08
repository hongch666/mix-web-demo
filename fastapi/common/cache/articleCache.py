import time
import hashlib
from typing import Optional, List, Dict, Any
from functools import lru_cache
from config.redis import get_redis_client
from common.utils import fileLogger as logger, Constants

# 全局单例实例
_article_cache_instance = None

class ArticleCache:
    """
    文章缓存管理 - 二级缓存架构
    
    缓存策略：
    1. L1 缓存（本地内存）- 5分钟 TTL
    2. L2 缓存（Redis）- 1天 TTL
    3. 版本号检测 - Hive 表变化时自动失效
    """
    
    # Redis 键前缀
    REDIS_KEY_PREFIX = "article:top10"
    REDIS_VERSION_KEY = "article:top10:version"
    
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
        return "ArticleCache()"
    
    def __str__(self) -> str:
        """字符串表示"""
        return "ArticleCache()"
    
    def get_cache_version(self, hive_conn) -> Optional[str]:
        """获取 Hive articles 表的版本号"""
        try:
            with hive_conn.cursor() as cursor:
                cursor.execute(Constants.HIVE_TABLE_VERSION_SQL)
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
            logger.info(Constants.L1_CACHE_TTL_EXPIRED)
            return False
        
        return True
    
    def get_from_local(self) -> Optional[List[Dict[str, Any]]]:
        """从本地缓存获取"""
        if self.is_local_cache_valid():
            cache_age = time.time() - self._local_cache_time
            logger.info(f"[L1缓存] 命中，缓存年龄: {cache_age:.1f}s")
            return self._local_cache
        return None
    
    def get_from_redis(self) -> Optional[List[Dict[str, Any]]]:
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
    
    def is_version_changed(self, hive_conn) -> bool:
        """检查版本号是否变化"""
        try:
            current_version = self.get_cache_version(hive_conn)
            if not current_version:
                logger.debug(Constants.SKIP_VERSION_CHECK)
                return False
            
            # 从 Redis 获取旧版本号（优先级最高）
            old_version = None
            if self._redis.is_available():
                try:
                    old_version = self._redis.get(self.REDIS_VERSION_KEY)
                    if old_version:
                        # 统一转换为字符串类型(Redis可能返回bytes)
                        old_version = old_version if isinstance(old_version, str) else old_version.decode('utf-8')
                except Exception as e:
                    logger.debug(f"[缓存] Redis 读取版本号失败: {e}")
                    old_version = None
            
            # 本地版本号作为备选
            if not old_version and self._cache_version:
                old_version = self._cache_version
            
            # 关键修复：如果没有旧版本号（首次调用），不认为是版本变化
            if not old_version:
                logger.debug(f"[缓存] 首次初始化，当前版本: {current_version}")
                return False
            
            # 版本号对比：有旧版本且不相等时才算变化
            if str(current_version) != str(old_version):
                logger.info(f"[缓存] 表版本已变化 (旧: {old_version} → 新: {current_version})")
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
            logger.info(Constants.VERSION_CHANGED_CLEAR_CACHE)
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
        logger.info(Constants.HIVE_CACHE_MISS_QUERY_HIVE_MESSAGE)
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
        logger.info(Constants.L1_CACHE_UPDATED)
        
        # 2. 更新 Redis 缓存
        try:
            if self._redis.is_available():
                self._redis.set(self.REDIS_KEY_PREFIX, data, ex=self._redis_ttl)
                logger.info(f"[L2缓存] 已更新 Redis，TTL={self._redis_ttl}s (1天)")
        except Exception as e:
            logger.error(f"[L2缓存] Redis 写入失败: {e}")
        
        # 3. 更新版本号
        try:
            version = self.get_cache_version(hive_conn)
            if version:
                self._cache_version = version
                if self._redis.is_available():
                    self._redis.set(self.REDIS_VERSION_KEY, version, ex=self._redis_ttl)
                logger.info(f"[缓存] 版本号已更新: {version}")
        except Exception as e:
            logger.warning(f"设置缓存版本号失败: {e}")
    
    def clear_all(self):
        """清除所有缓存"""
        # 清除本地缓存
        self._local_cache = None
        self._local_cache_time = 0
        self._cache_version = None
        logger.info(Constants.L1_CACHE_CLEARED)
        
        # 清除 Redis 缓存
        try:
            if self._redis.is_available():
                self._redis.delete(self.REDIS_KEY_PREFIX, self.REDIS_VERSION_KEY)
                logger.info(Constants.L2_CACHE_CLEARED)
        except Exception as e:
            logger.error(f"[L2缓存] Redis 清除失败: {e}")

@lru_cache()
def get_article_cache() -> ArticleCache:
    """获取 ArticleCache 单例实例"""
    global _article_cache_instance
    if _article_cache_instance is None:
        _article_cache_instance = ArticleCache()
    return _article_cache_instance
