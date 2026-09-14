import hashlib
from contextvars import ContextVar
from typing import Any, Optional

from app.core.base import Logger
from app.core.constants import Messages, Scripts
from app.core.db import execute_clickhouse_query

from .baseCache import BaseCache

# 按版本键记录本次读取缓存时观察到的数仓版本，供写缓存时提交
# 缓存实例是单例，用实例属性会在并发请求间交叉覆盖，因此用 ContextVar 按协程隔离
_READ_VERSIONS: ContextVar[Optional[dict[str, str]]] = ContextVar(
    "cache_read_versions", default=None
)


class VersionedCache(BaseCache):
    """
    带版本控制的缓存模板类

    在基础缓存上增加版本号检测，数仓表变化时自动失效
    """

    # 子类需要定义这两个常量
    REDIS_VERSION_KEY: str = ""

    # 版本号校验依据的数仓模型，直接取模型对应表（如 AdsTop10Article 对应 warehouse.ads_top10_articles）
    VERSION_MODEL: Optional[type[Any]] = None

    def __init__(self) -> None:
        super().__init__()
        # 版本号
        self._cache_version: Optional[str] = None

    def _remember_read_version(self, version: str) -> None:
        """记录本次读取观察到的版本，供写缓存时提交"""
        versions: dict[str, str] = dict(_READ_VERSIONS.get() or {})
        versions[self.REDIS_VERSION_KEY] = version
        _READ_VERSIONS.set(versions)

    def _take_read_version(self) -> Optional[str]:
        """取出并清除本次读取观察到的版本，避免被后续无关写入复用"""
        versions: dict[str, str] = dict(_READ_VERSIONS.get() or {})
        version: Optional[str] = versions.pop(self.REDIS_VERSION_KEY, None)
        _READ_VERSIONS.set(versions)
        return version

    async def get_cache_version(self) -> Optional[str]:
        """基于版本号校验模型对应表的内容生成稳定版本号"""
        if self.VERSION_MODEL is None:
            Logger.warning(
                Messages.CACHE_VERSION_MODEL_NOT_SET(type(self).__name__)
            )
            return None

        try:
            ch_table: str = self.VERSION_MODEL.__table__.fullname
            # SQL 模板统一收敛在 core/constants/scripts.py
            query = Scripts.CACHE_VERSION_CLICKHOUSE_QUERY(ch_table)
            result = await execute_clickhouse_query(query)
            if not result:
                return None

            total_rows, max_stat_ts = result[0]
            version_str = f"{ch_table}:{int(total_rows)}:{int(max_stat_ts)}"
            return hashlib.md5(version_str.encode()).hexdigest()[:8]
        except Exception as e:
            Logger.debug(Messages.CACHE_VERSION_GET_FAILED(e))
            return None

    async def _persist_version(self, version: str) -> None:
        """同步更新本地版本号，并尽量写入 Redis"""
        self._cache_version = version
        await self._redis.set(self.REDIS_VERSION_KEY, version, ex=self._redis_ttl)

    async def is_version_changed(self) -> bool:
        """检查版本号是否变化"""
        try:
            current_version = await self.get_cache_version()
            if not current_version:
                Logger.debug(Messages.SKIP_VERSION_CHECK)
                return False

            # 记录本次读取观察到的版本，写缓存时以此为版本号，避免旧数据被绑定新版本
            self._remember_read_version(current_version)

            # 从 Redis 获取旧版本号（优先级最高）
            old_version = None
            try:
                old_version = await self._redis.get(self.REDIS_VERSION_KEY)
                if old_version:
                    # 统一转换为字符串类型(Redis可能返回bytes)
                    old_version = (
                        old_version
                        if isinstance(old_version, str)
                        else old_version.decode("utf-8")
                    )
            except Exception as e:
                Logger.debug(Messages.CACHE_VERSION_REDIS_READ_FAILED(e))
                old_version = None

            # 本地版本号作为备选
            if not old_version and self._cache_version:
                old_version = self._cache_version

            # 关键修复：如果没有旧版本号（首次调用），不认为是版本变化
            if not old_version:
                await self._persist_version(current_version)
                Logger.debug(Messages.CACHE_VERSION_INITIALIZED(current_version))
                return False

            # 版本号对比：有旧版本且不相等时才算变化
            if str(current_version) != str(old_version):
                Logger.info(
                    Messages.CACHE_VERSION_CHANGED(
                        str(old_version), str(current_version)
                    )
                )
                return True

            return False
        except Exception as e:
            Logger.warning(Messages.CACHE_VERSION_CHECK_FAILED(e))
            return False

    async def update_version(self) -> None:
        """提交缓存数据的版本号

        读取数据到写入缓存之间数仓可能已完成刷新，此时若取当前最新版本，会把刷新前
        读到的旧数据与刷新后的新版本绑定，导致版本校验长期判定为未变化而缓存无法失效，
        因此优先提交读取时观察到的版本，仅在缺少读取上下文（如预热直接写缓存）时回退实时计算
        """
        try:
            version: Optional[str] = self._take_read_version()
            if not version:
                version = await self.get_cache_version()
            if version:
                await self._persist_version(version)
                Logger.info(Messages.CACHE_VERSION_UPDATED(version))
        except Exception as e:
            Logger.warning(Messages.CACHE_VERSION_SET_FAILED(e))

    async def clear_all(self) -> None:
        """清除所有缓存，包括版本号"""
        self._cache_version = None
        await super().clear_all()
        try:
            await self._redis.delete(self.REDIS_VERSION_KEY)
        except Exception as e:
            Logger.error(Messages.CACHE_VERSION_CLEAR_FAILED(e))
