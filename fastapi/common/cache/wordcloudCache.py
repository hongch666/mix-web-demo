import time
from typing import Optional
from common.config import get_redis_client
from common.utils import fileLogger as logger, Constants

# 全局单例实例
_wordcloud_cache_instance = None

class WordcloudCache:
    """
    词云图缓存管理 - Redis缓存
    
    缓存策略：
    - 使用Redis缓存词云图OSS URL
    - TTL: 24小时
    - 键: wordcloud:url
    """
    
    # Redis 键
    REDIS_KEY = "wordcloud:url"
    
    def __init__(self) -> None:
        # Redis 客户端
        self._redis = get_redis_client()
        
        # Redis TTL（24小时）
        self._redis_ttl: int = 86400
    
    def __repr__(self) -> str:
        """对象表示 - 用于日志输出和序列化"""
        return "WordcloudCache()"
    
    def __str__(self) -> str:
        """字符串表示"""
        return "WordcloudCache()"
    
    def get(self) -> Optional[str]:
        """
        从Redis获取词云图OSS URL
        
        返回:
            - 如果缓存存在，返回OSS URL
            - 如果缓存不存在，返回None
        """
        try:
            if not self._redis:
                logger.warning(Constants.REDIS_CACHE_CLEARED)
                return None
            
            start = time.time()
            cached_url = self._redis.get(self.REDIS_KEY)
            
            if cached_url:
                elapsed = time.time() - start
                logger.info(f"词云图缓存命中，获取耗时 {elapsed:.3f}s")
                return cached_url.decode('utf-8') if isinstance(cached_url, bytes) else cached_url
            
            logger.debug(Constants.WORDCLOUD_CACHE_MISS)
            return None
        except Exception as e:
            logger.warning(f"从Redis获取词云图缓存失败: {e}")
            return None
    
    def set(self, oss_url: str) -> bool:
        """
        将词云图OSS URL缓存到Redis
        
        参数:
            oss_url: OSS中词云图的URL
        
        返回:
            - True: 缓存设置成功
            - False: 缓存设置失败
        """
        try:
            if not self._redis:
                logger.warning(Constants.REDIS_CACHE_CLEARED)
                return False
            
            start = time.time()
            self._redis.set(self.REDIS_KEY, oss_url, ex=self._redis_ttl)
            elapsed = time.time() - start
            logger.info(f"词云图URL已缓存到Redis，TTL: {self._redis_ttl}s，设置耗时 {elapsed:.3f}s")
            return True
        except Exception as e:
            logger.error(f"将词云图URL缓存到Redis失败: {e}")
            return False
    
    def delete(self) -> bool:
        """
        删除Redis中的词云图缓存
        
        返回:
            - True: 删除成功
            - False: 删除失败
        """
        try:
            if not self._redis:
                logger.warning(Constants.REDIS_CACHE_CLEARED)
                return False
            
            self._redis.delete(self.REDIS_KEY)
            logger.info(Constants.WORDCLOUD_CACHE_DELETED)
            return True
        except Exception as e:
            logger.error(f"删除词云图缓存失败: {e}")
            return False


def get_wordcloud_cache() -> WordcloudCache:
    """依赖注入 - 获取词云图缓存单例"""
    global _wordcloud_cache_instance
    if _wordcloud_cache_instance is None:
        _wordcloud_cache_instance = WordcloudCache()
    return _wordcloud_cache_instance
