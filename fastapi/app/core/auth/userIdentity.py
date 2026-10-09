from typing import Any, Optional


def normalize_user_id(user_id: Any) -> Optional[int]:
    """将用户ID统一转换为整数，空值、空串与非法值返回 None"""
    if user_id is None:
        return None
    try:
        user_id_text = str(user_id).strip()
        if not user_id_text:
            return None
        return int(user_id_text)
    except (TypeError, ValueError):
        return None


def is_memory_user(user_id: Any) -> bool:
    """判断是否为可承载聊天记忆的真实用户

    系统调用身份（userId 小于等于 0，未登录时取 Defaults.SYSTEM_USER_ID）
    不参与聊天记忆读写，否则所有未登录请求会共用同一个记忆桶
    """
    normalized = normalize_user_id(user_id)
    return normalized is not None and normalized > 0
