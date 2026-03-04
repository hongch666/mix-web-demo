from typing import Any, Dict, Optional


def success(
    data: Optional[Any] = None, msg: str = "success", code: int = 1
) -> Dict[str, Any]:
    """返回成功响应

    Args:
        data: 返回数据, 默认为 None
        msg: 返回消息, 默认为 'success'
        code: 返回状态码, 默认为 1

    Returns:
        包含 code, data, msg 的字典
    """
    return {"code": code, "data": data, "msg": msg}


def error(
    msg: str = "error", code: int = 0, data: Optional[Any] = None
) -> Dict[str, Any]:
    """返回错误响应

    Args:
        msg: 错误消息, 默认为 'error'
        code: 错误代码, 默认为 0
        data: 附加数据, 默认为 None

    Returns:
        包含 code, data, msg 的字典
    """
    return {"code": code, "data": data, "msg": msg}
