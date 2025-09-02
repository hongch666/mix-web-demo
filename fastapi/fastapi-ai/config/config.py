import os
from typing import Any, Dict, Optional
import yaml

def load_config(section: Optional[str] = None, key: Optional[str] = None) -> Any:
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "application.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config: Dict[str, Any] = yaml.safe_load(f)
    if section is None:
        return config
    if key is None:
        return config.get(section)
    return config.get(section, {}).get(key)

def load_secret_config(section: Optional[str] = None, key: Optional[str] = None) -> Any:
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "application-secret.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config: Dict[str, Any] = yaml.safe_load(f)
    if section is None:
        return config
    if key is None:
        return config.get(section)
    return config.get(section, {}).get(key)