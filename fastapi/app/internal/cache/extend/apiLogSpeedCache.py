from functools import lru_cache
from typing import Any, ClassVar, Optional

from app.core.base import LoggerProtocol
from app.core.constants import Messages, RedisKeys
from app.internal.models import AdsApiAverageSpeed

from ..versionedCache import VersionedCache

# 全局单例实例
_api_log_speed_cache_instance = None


class ApiLogSpeedCache(VersionedCache):
    """
    接口平均响应时间缓存 - 二级缓存架构（带版本控制）

    缓存策略：
    1. L1 缓存（本地内存）- 5分钟 TTL
    2. L2 缓存（Redis）- 1天 TTL
    3. 版本号检测 - 数仓平均响应时间表变化时自动失效
    """

    REDIS_KEY_PREFIX: str = RedisKeys.APILOG_AVERAGE_SPEED
    REDIS_VERSION_KEY: str = RedisKeys.APILOG_AVERAGE_SPEED_VERSION
    L1_CACHE_TTL: int = 300

    # 版本号校验依据：接口平均响应时间数仓表
    VERSION_MODEL: ClassVar[type[AdsApiAverageSpeed]] = AdsApiAverageSpeed

    async def get(self) -> Optional[list[dict[str, Any]]]:
        """获取缓存：先校验版本号，再依次查本地与 Redis"""
        if await self.is_version_changed():
            self._logger.info(Messages.VERSION_CHANGED_CLEAR_CACHE)
            await self.clear_all()
            return None

        local_data = await self.get_from_local()
        if local_data:
            return local_data

        return await self.get_from_redis()

    async def set(self, data: list[dict[str, Any]]) -> None:
        """同时写入两级缓存并提交版本号"""
        await self.update_local_cache(data)
        await self.update_redis_cache(data)
        await self.update_version()


@lru_cache
def get_api_log_speed_cache(logger: LoggerProtocol | None = None) -> ApiLogSpeedCache:
    """获取 ApiLogSpeedCache 单例实例"""
    global _api_log_speed_cache_instance
    if _api_log_speed_cache_instance is None:
        _api_log_speed_cache_instance = ApiLogSpeedCache(logger)
    return _api_log_speed_cache_instance
