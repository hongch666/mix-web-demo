from datetime import UTC, datetime, timedelta
from typing import Any, Optional

import jwt
from jwt import PyJWTError

from app.core.constants import HttpCode, Messages

from ..config import load_config
from ..errors import BusinessException


class InternalTokenUtil:
    """内部服务令牌工具类，用于生成和验证内部服务之间通信的JWT令牌"""

    _instance: Optional["InternalTokenUtil"] = None
    _initialized: bool = False
    _secret: str = ""
    _expiration: int = 0

    def __new__(cls) -> "InternalTokenUtil":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初始化 JWT 密钥和过期时间"""
        if not InternalTokenUtil._initialized:
            config: dict[str, Any] = load_config("internal_token")
            secret: Optional[str] = config.get("secret")
            expiration: Optional[int] = config.get("expiration")

            if not secret:
                raise BusinessException(
                    Messages.INTERNAL_TOKEN_SECRET_NOT_NULL,
                    HttpCode.INTERNAL_SERVER_ERROR,
                    Messages.ERROR_INTERNAL_TOKEN_SECRET_NOT_NULL,
                )

            if expiration is None:
                raise BusinessException(
                    Messages.INTERNAL_TOKEN_EXPIRATION_NOT_SET,
                    HttpCode.INTERNAL_SERVER_ERROR,
                    Messages.ERROR_INTERNAL_TOKEN_EXPIRATION_NOT_SET,
                )

            InternalTokenUtil._secret = secret
            InternalTokenUtil._expiration = expiration
            InternalTokenUtil._initialized = True

    def generate_internal_token(self, user_id: int, service_name: str) -> str:
        """
        生成内部服务令牌

        :param user_id: 用户ID（-1表示系统调用）
        :param service_name: 服务名称
        :return: JWT令牌字符串
        """
        payload: dict[str, Any] = {
            "userId": user_id,
            "serviceName": service_name,
            "tokenType": "internal",
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC)
            + timedelta(milliseconds=InternalTokenUtil._expiration),
        }
        return jwt.encode(payload, InternalTokenUtil._secret, algorithm="HS256")

    def validate_internal_token(self, token: str) -> dict[str, Any]:
        """
        验证内部服务令牌

        :param token: JWT令牌字符串
        :return: 验证成功返回解密后的声明，失败抛出异常
        """
        try:
            decoded: dict[str, Any] = jwt.decode(
                token, InternalTokenUtil._secret, algorithms=["HS256"]
            )
            return decoded
        except jwt.ExpiredSignatureError as error:
            raise BusinessException(
                Messages.INTERNAL_TOKEN_EXPIRED,
                HttpCode.UNAUTHORIZED,
                Messages.ERROR_INTERNAL_TOKEN_EXPIRED,
            ) from error
        except PyJWTError as error:
            raise BusinessException(
                Messages.INTERNAL_TOKEN_INVALID,
                HttpCode.UNAUTHORIZED,
                Messages.ERROR_INTERNAL_TOKEN_INVALID,
            ) from error

    def extract_user_id(self, token: str) -> Optional[int]:
        """
        从令牌中提取用户ID

        :param token: JWT令牌字符串
        :return: 用户ID
        """
        claims: dict[str, Any] = self.validate_internal_token(token)
        return claims.get("userId")  # type: ignore[return-value]

    def extract_service_name(self, token: str) -> Optional[str]:
        """
        从令牌中提取服务名称

        :param token: JWT令牌字符串
        :return: 服务名称
        """
        claims: dict[str, Any] = self.validate_internal_token(token)
        return claims.get("serviceName")  # type: ignore[return-value]
