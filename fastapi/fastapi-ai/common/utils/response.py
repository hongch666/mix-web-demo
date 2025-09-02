from typing import Any, Optional, Dict

def success(data: Optional[Any] = None, msg: str = "success", code: int = 1) -> Dict[str, Any]:
    return {
        "code": code,
        "data": data,
        "msg": msg
    }

def fail(msg: str = "error", code: int = 0, data: Optional[Any] = None) -> Dict[str, Any]:
    return {
        "code": code,
        "data": data,
        "msg": msg
    }
