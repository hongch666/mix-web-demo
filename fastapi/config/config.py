import os
import yaml

def load_config(section=None, key=None):
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "application.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if section is None:
        return config
    if key is None:
        return config.get(section)
    return config.get(section, {}).get(key)