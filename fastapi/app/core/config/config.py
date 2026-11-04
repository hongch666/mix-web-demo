import os
import re
from functools import lru_cache
from io import StringIO
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv

from app.core.constants import Messages

# 在应用启动时加载 .env 文件
load_dotenv()


def resolve_env_vars_in_string(text: str) -> str:
    """
    替换字符串中的环境变量占位符
    支持格式：${VAR_NAME:default_value} 或 ${VAR_NAME}
    """
    pattern: str = r"\$\{([^:}]+)(?::([^}]*))?\}"

    def replace_var(match: re.Match[str]) -> str:
        """将单个环境变量占位符替换为对应环境变量值，未设置时使用默认值"""
        var_name: str = match.group(1)
        default_value: str = match.group(2) or ""
        return os.getenv(var_name, default_value)

    return re.sub(pattern, replace_var, text)


@lru_cache(maxsize=1)
def _resolve_config_path() -> Path:
    """定位 application.yaml 路径，结果按进程缓存避免高频读配置重复做路径探测"""
    current_file: Path = Path(__file__).resolve()
    candidates = [
        current_file.parents[3] / "application.yaml",  # fastapi/application.yaml
        current_file.parents[2]
        / "application.yaml",  # app/application.yaml（兼容历史结构）
        Path.cwd() / "application.yaml",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    searched = "\n".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(Messages.CONFIG_FILE_NOT_FOUND(searched))


@lru_cache(maxsize=1)
def _load_config_document() -> dict[str, Any]:
    """读取并解析 application.yaml，结果按进程缓存，避免每次调用都读盘与做 YAML 解析"""
    config_path: Path = _resolve_config_path()

    # 读取原始文件
    with open(config_path, encoding="utf-8") as f:
        content: str = f.read()

    # 替换环境变量占位符
    content = resolve_env_vars_in_string(content)

    # 用替换后的内容解析 YAML
    config: Optional[dict[str, Any]] = yaml.safe_load(StringIO(content))
    return config or {}


def clear_config_cache() -> None:
    """清空配置缓存，供测试与需要重新读取配置的场景使用

    测试中可能把定位函数替换为普通函数，因此逐个探测 cache_clear 后再调用
    """
    for cached in (_resolve_config_path, _load_config_document):
        clear = getattr(cached, "cache_clear", None)
        if callable(clear):
            clear()


def load_config(section: Optional[str] = None, key: Optional[str] = None) -> Any:
    """
    加载 application.yaml 配置文件并解析环境变量

    读取结果按进程缓存，调用方只读不写，禁止修改返回的字典内容
    """
    config: dict[str, Any] = _load_config_document()

    if section is None:
        return config
    if key is None:
        return config.get(section)
    return (config.get(section) or {}).get(key)
