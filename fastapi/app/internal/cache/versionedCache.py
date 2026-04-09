import asyncio
import hashlib
from typing import Any, Optional

from app.core.base import Constants, Logger
from app.core.config import load_config

from .baseCache import BaseCache


class VersionedCache(BaseCache):
    """
    带版本控制的缓存模板类

    在基础缓存上增加版本号检测，表变化时自动失效
    """

    # 子类需要定义这个常量
    REDIS_VERSION_KEY: str = ""

    def __init__(self) -> None:
        super().__init__()
        # 版本号
        self._cache_version: Optional[str] = None

    async def get_cache_version(self, ch_conn: Any) -> Optional[str]:
        """基于 ClickHouse 表内容生成稳定版本号。"""
        try:
            if ch_conn is None:
                return None
            ch_table = load_config("database")["clickhouse"]["table"]
            ch_db = load_config("database")["clickhouse"]["database"]
            query = f"""
                SELECT
                    count() AS total_rows,
                    ifNull(max(toUnixTimestamp(update_at)), 0) AS max_update_ts,
                    ifNull(max(id), 0) AS max_id
                FROM {ch_db}.{ch_table}
            """
            result = await asyncio.to_thread(ch_conn.execute, query)
            if not result:
                return None

            total_rows, max_update_ts, max_id = result[0]
            version_str = (
                f"{ch_db}.{ch_table}:{int(total_rows)}:{int(max_update_ts)}:{int(max_id)}"
            )
            return hashlib.md5(version_str.encode()).hexdigest()[:8]
        except Exception as e:
            Logger.debug(f"获取版本号失败: {type(e).__name__}: {e}")
            return None

    async def _persist_version(self, version: str) -> None:
        """同步更新本地版本号，并尽量写入 Redis。"""
        self._cache_version = version
        await self._redis.set(self.REDIS_VERSION_KEY, version, ex=self._redis_ttl)

    async def is_version_changed(self, ch_conn: Any) -> bool:
        """检查版本号是否变化"""
        try:
            current_version = await self.get_cache_version(ch_conn)
            if not current_version:
                Logger.debug(Constants.SKIP_VERSION_CHECK)
                return False

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
                Logger.debug(f"[缓存] Redis 读取版本号失败: {e}")
                old_version = None

            # 本地版本号作为备选
            if not old_version and self._cache_version:
                old_version = self._cache_version

            # 关键修复：如果没有旧版本号（首次调用），不认为是版本变化
            if not old_version:
                await self._persist_version(current_version)
                Logger.debug(f"[缓存] 首次初始化，当前版本: {current_version}")
                return False

            # 版本号对比：有旧版本且不相等时才算变化
            if str(current_version) != str(old_version):
                Logger.info(
                    f"[缓存] 表版本已变化 (旧: {old_version} → 新: {current_version})"
                )
                return True

            return False
        except Exception as e:
            Logger.warning(f"版本检测异常: {e}")
            return False

    async def update_version(self, ch_conn: Any) -> None:
        """更新版本号"""
        try:
            version = await self.get_cache_version(ch_conn)
            if version:
                await self._persist_version(version)
                Logger.info(f"[缓存] 版本号已更新: {version}")
        except Exception as e:
            Logger.warning(f"设置缓存版本号失败: {e}")

    async def clear_all(self) -> None:
        """清除所有缓存，包括版本号"""
        self._cache_version = None
        await super().clear_all()
        try:
            await self._redis.delete(self.REDIS_VERSION_KEY)
        except Exception as e:
            Logger.error(f"[L2缓存] Redis 清除版本号失败: {e}")
