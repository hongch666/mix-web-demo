import os
from typing import Any, Dict, Optional
import yaml
import re
from io import StringIO
from dotenv import load_dotenv

# 在应用启动时加载 .env 文件
load_dotenv()

def resolve_env_vars_in_string(text: str) -> str:
    """
    替换字符串中的环境变量占位符
    支持格式：${VAR_NAME:default_value} 或 ${VAR_NAME}
    """
    pattern: str = r'\$\{([^:}]+)(?::([^}]*))?\}'
    def replace_var(match: re.Match[str]) -> str:
        var_name: str = match.group(1)
        default_value: str = match.group(2) or ""
        return os.getenv(var_name, default_value)
    return re.sub(pattern, replace_var, text)

def load_config(section: Optional[str] = None, key: Optional[str] = None) -> Any:
    """
    加载 application.yaml 配置文件并解析环境变量
    """
    config_path: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "../application.yaml")
    
    # 读取原始文件
    with open(config_path, "r", encoding="utf-8") as f:
        content: str = f.read()
    
    # 替换环境变量占位符
    content = resolve_env_vars_in_string(content)
    
    # 用替换后的内容解析 YAML
    config: Dict[str, Any] = yaml.safe_load(StringIO(content))
    
    if section is None:
        return config
    if key is None:
        return config.get(section)
    return config.get(section, {}).get(key)