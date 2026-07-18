from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.core.config import load_config
from app.core.constants import Scripts


@dataclass
class LangSmithConfig:
    """LangSmith 可观测性配置

    所有配置项通过 application.yaml + 环境变量加载，遵循项目统一配置规范。
    """

    enabled: bool = False
    api_key: str = ""
    project: str = "mix-web-demo-dev"
    endpoint: str = "https://api.smith.langchain.com"
    workspace_id: Optional[str] = None
    hide_inputs: bool = False
    hide_outputs: bool = False
    sampling_rate: float = 1.0

    # 脱敏配置
    max_string_length: int = Scripts.SANITIZER_MAX_STRING_LENGTH
    max_list_length: int = Scripts.SANITIZER_MAX_LIST_LENGTH
    max_dict_depth: int = Scripts.SANITIZER_MAX_DICT_DEPTH


def load_langsmith_config() -> LangSmithConfig:
    """从 application.yaml 加载 LangSmith 配置

    application.yaml 中的 ${VAR:default} 由 load_config 解析环境变量。
    默认关闭追踪，API Key 缺失时强制禁用。
    """
    cfg: Dict[str, Any] = load_config("langsmith") or {}

    enabled = str(cfg.get("enabled", "false")).lower() == "true"
    api_key = str(cfg.get("api_key", "")).strip()

    # 仅当显式开启且 API Key 存在时才启用
    if not api_key:
        enabled = False

    return LangSmithConfig(
        enabled=enabled,
        api_key=api_key,
        project=str(cfg.get("project", "mix-web-demo-dev")).strip(),
        endpoint=str(cfg.get("endpoint", "https://api.smith.langchain.com")).strip(),
        workspace_id=cfg.get("workspace_id") or None,
        hide_inputs=str(cfg.get("hide_inputs", "false")).lower() == "true",
        hide_outputs=str(cfg.get("hide_outputs", "false")).lower() == "true",
        sampling_rate=float(cfg.get("sampling_rate", 1.0)),
    )
