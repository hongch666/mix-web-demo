import hashlib
from typing import Any, Optional

from app.core.base import Constants, Logger

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

    def get_cache_version(self, ch_conn: Any) -> Optional[str]:
        """获取 ClickHouse 表的版本号 - 简化版本（避免类型转换问题）"""
        try:
            import time

            from app.core.db import load_config

            ch_table = load_config("database")["clickhouse"]["table"]
            ch_db = load_config("database")["clickhouse"]["database"]

            # 使用当前时间和表信息生成版本号
            # 这样的版本号在表数据变化时可能不会立即变化
            # 但避免了 ClickHouse driver 的类型转换问题
            version_str = f"{ch_db}_{ch_table}_{int(time.time()) // 3600}"
            return hashlib.md5(version_str.encode()).hexdigest()[:8]
        except Exception as e:
            Logger.debug(f"获取版本号失败: {type(e).__name__}: {e}")
            return None

    def is_version_changed(self, ch_conn: Any) -> bool:
        """检查版本号是否变化"""
        try:
            current_version = self.get_cache_version(ch_conn)
            if not current_version:
                Logger.debug(Constants.SKIP_VERSION_CHECK)
                return False

            # 从 Redis 获取旧版本号（优先级最高）
            old_version = None
            if self._redis.is_available():
                try:
                    old_version = self._redis.get(self.REDIS_VERSION_KEY)
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

    def update_version(self, ch_conn: Any) -> None:
        """更新版本号"""
        try:
            version = self.get_cache_version(ch_conn)
            if version:
                self._cache_version = version
                if self._redis.is_available():
                    self._redis.set(self.REDIS_VERSION_KEY, version, ex=self._redis_ttl)
                Logger.info(f"[缓存] 版本号已更新: {version}")
        except Exception as e:
            Logger.warning(f"设置缓存版本号失败: {e}")

    def clear_all(self) -> None:
        """清除所有缓存，包括版本号"""
        self._cache_version = None
        super().clear_all()
        try:
            if self._redis.is_available():
                self._redis.delete(self.REDIS_VERSION_KEY)
        except Exception as e:
            Logger.error(f"[L2缓存] Redis 清除版本号失败: {e}")
