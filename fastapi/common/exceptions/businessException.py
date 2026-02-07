from typing import Optional

class BusinessException(Exception):
    """业务异常 - 用于返回可向客户端显示的错误信息"""

    def __init__(self, message: str, status_code: int = 200) -> None:
        """
        初始化业务异常

        Args:
            message: 返回给客户端的错误信息
            status_code: HTTP 状态码，默认 200
        """
        self.message: str = message
        self.status_code: int = status_code
        super().__init__(self.message)
