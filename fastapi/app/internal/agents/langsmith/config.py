from dataclasses import dataclass
from typing import Any, Optional

from app.core.config import load_config
from app.core.constants import Scripts


@dataclass
class LangSmithConfig:
    """LangSmith 可观测性配置

    所有配置项通过 application.yaml + 环境变量加载，遵循项目统一配置规范。
    """

    enabled: bool
    api_key: str
    project: str
    endpoint: str
    workspace_id: Optional[str]
    hide_inputs: bool
    hide_outputs: bool
    sampling_rate: float

    # 脱敏配置
    max_string_length: int = Scripts.SANITIZER_MAX_STRING_LENGTH
    max_list_length: int = Scripts.SANITIZER_MAX_LIST_LENGTH
    max_dict_depth: int = Scripts.SANITIZER_MAX_DICT_DEPTH


def load_langsmith_config() -> LangSmithConfig:
    """从 application.yaml 加载 LangSmith 配置

    application.yaml 中的 ${VAR:default} 由 load_config 解析环境变量。
    默认关闭追踪，API Key 缺失时强制禁用。
    """
    cfg: dict[str, Any] = load_config("langsmith") or {}

    enabled = str(cfg["enabled"]).lower() == "true"
    api_key = str(cfg["api_key"]).strip()

    # 仅当显式开启且 API Key 存在时才启用
    if not api_key:
        enabled = False

    return LangSmithConfig(
        enabled=enabled,
        api_key=api_key,
        project=str(cfg["project"]).strip(),
        endpoint=str(cfg["endpoint"]).strip(),
        workspace_id=cfg["workspace_id"] or None,
        hide_inputs=str(cfg["hide_inputs"]).lower() == "true",
        hide_outputs=str(cfg["hide_outputs"]).lower() == "true",
        sampling_rate=float(cfg["sampling_rate"]),
    )
