import hashlib
import hmac
import os
import re
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.constants import Scripts

# 通过 HMAC 对用户 ID 进行不可逆哈希
_user_hash_hmac_key: Optional[bytes] = None


def _get_hmac_key() -> bytes:
    """获取或生成用户 ID 哈希密钥"""
    global _user_hash_hmac_key
    if _user_hash_hmac_key is None:
        raw = os.getenv("LANGSMITH_USER_HASH_KEY") or str(uuid4())
        _user_hash_hmac_key = raw.encode("utf-8")
    return _user_hash_hmac_key


def sanitize_user_id(user_id: str) -> str:
    """对用户 ID 进行不可逆哈希，用于聚合而不能反推原 ID"""
    if not user_id:
        return "anonymous"
    key = _get_hmac_key()
    digest = hmac.new(key, user_id.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"u_{digest[:16]}"


def _is_sensitive_key(key: str) -> bool:
    """判断键名是否为敏感字段"""
    key_lower = str(key).lower()
    for pattern in Scripts.SENSITIVE_KEY_PATTERNS:
        if pattern in key_lower:
            return True
    return False


def _sanitize_string(value: str) -> str:
    """截断超长字符串并掩码邮箱和手机号"""
    max_len = Scripts.SANITIZER_MAX_STRING_LENGTH
    # 掩码邮箱
    value = re.sub(
        r"([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
        r"\1@***",
        value,
    )
    # 掩码手机号 (中国大陆)
    value = re.sub(
        r"1[3-9]\d{9}", lambda m: m.group()[:3] + "****" + m.group()[-4:], value
    )
    if len(value) > max_len:
        value = value[:max_len] + f"...[截断,原长{len(value)}]"
    return value


def sanitize_metadata(
    metadata: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """递归脱敏 metadata 字典，删除敏感键、截断长值

    Args:
        metadata: 原始 metadata 字典

    Returns:
        脱敏后的 metadata 字典
    """
    if metadata is None:
        return None
    return _sanitize_dict(metadata, depth=0)


def sanitize_tool_input(tool_input: Any) -> str:
    """脱敏工具输入，只保留工具名和结构摘要

    Args:
        tool_input: 工具原始输入

    Returns:
        脱敏后的工具输入摘要字符串
    """
    if isinstance(tool_input, str):
        return _sanitize_string(tool_input)
    if isinstance(tool_input, dict):
        safe_dict = _sanitize_dict(tool_input, depth=0)
        return str(safe_dict) if safe_dict else "[工具输入已隐藏]"
    return f"[{type(tool_input).__name__} 类型输入已隐藏]"


def sanitize_tool_output(output: Any) -> str:
    """脱敏工具输出，仅保留输出长度和状态摘要

    Args:
        output: 工具原始输出

    Returns:
        脱敏后的工具输出摘要字符串
    """
    text = str(output) if output is not None else ""
    if len(text) > Scripts.SANITIZER_MAX_STRING_LENGTH:
        return f"[输出已截断, 原长 {len(text)}] {text[:100]}..."
    return f"[工具输出, 长度: {len(text)}]"


def _sanitize_dict(
    data: Dict[str, Any],
    depth: int,
) -> Dict[str, Any]:
    """递归脱敏字典"""
    if depth > Scripts.SANITIZER_MAX_DICT_DEPTH:
        return {"_truncated": f"超过最大深度 {Scripts.SANITIZER_MAX_DICT_DEPTH}"}

    result: Dict[str, Any] = {}
    for key, value in data.items():
        if _is_sensitive_key(key):
            result[key] = "***已脱敏***"
            continue

        if isinstance(value, str):
            result[key] = _sanitize_string(value)
        elif isinstance(value, dict):
            result[key] = _sanitize_dict(value, depth + 1)
        elif isinstance(value, list):
            result[key] = _sanitize_list(value, depth + 1)
        elif isinstance(value, (int, float, bool, type(None))):
            result[key] = value
        else:
            result[key] = str(value)
    return result


def _sanitize_list(
    data: List[Any],
    depth: int,
) -> List[Any]:
    """递归脱敏列表，限制最大长度"""
    if depth > Scripts.SANITIZER_MAX_DICT_DEPTH:
        return [f"[超过最大深度 {Scripts.SANITIZER_MAX_DICT_DEPTH}]"]

    result: List[Any] = []
    for i, item in enumerate(data):
        if i >= Scripts.SANITIZER_MAX_LIST_LENGTH:
            result.append(f"...[截断, 共 {len(data)} 项]")
            break
        if isinstance(item, str):
            result.append(_sanitize_string(item))
        elif isinstance(item, dict):
            result.append(_sanitize_dict(item, depth))
        elif isinstance(item, list):
            result.append(_sanitize_list(item, depth))
        elif isinstance(item, (int, float, bool, type(None))):
            result.append(item)
        else:
            result.append(str(item))
    return result
