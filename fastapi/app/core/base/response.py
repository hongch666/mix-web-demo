from typing import Any, Dict, Optional

from fastapi.encoders import jsonable_encoder

from .httpCode import HttpCode


def success(
    data: Optional[Any] = None, msg: str = "success"
) -> Dict[str, Any]:
    """返回成功响应

    Args:
        data: 返回数据, 默认为 None
        msg: 返回消息, 默认为 'success'

    Returns:
        包含 code, data, msg 的字典
    """
    return jsonable_encoder({"code": HttpCode.OK, "data": data, "msg": msg})


def error(
    code: int = HttpCode.INTERNAL_SERVER_ERROR,
    msg: str = "error",
    data: Optional[Any] = None,
) -> Dict[str, Any]:
    """返回错误响应

    Args:
        code: 3 位 HTTP 状态码, 默认为 500
        msg: 错误消息, 默认为 'error'
        data: 附加数据, 默认为 None

    Returns:
        包含 code, data, msg 的字典
    """
    return jsonable_encoder({"code": code, "data": data, "msg": msg})
