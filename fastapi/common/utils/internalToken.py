import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from common.exceptions import BusinessException
from common.utils import Constants
from common.config import load_config


class InternalTokenUtil:
    """内部服务令牌工具类，用于生成和验证内部服务之间通信的JWT令牌"""

    _instance: Optional['InternalTokenUtil'] = None
    _initialized: bool = False
    _secret: Optional[str] = None
    _expiration: Optional[int] = None

    def __new__(cls) -> 'InternalTokenUtil':
        if cls._instance is None:
            cls._instance = super(InternalTokenUtil, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初始化 JWT 密钥和过期时间"""
        if not InternalTokenUtil._initialized:
            config: Dict[str, Any] = load_config("internal_token")
            InternalTokenUtil._secret = config.get("secret")
            InternalTokenUtil._expiration = config.get("expiration")

            if not InternalTokenUtil._secret:
                raise BusinessException(Constants.INTERNAL_TOKEN_SECRET_NOT_NULL)

            InternalTokenUtil._initialized = True

    def generate_internal_token(self, user_id: int, service_name: str) -> str:
        """
        生成内部服务令牌

        :param user_id: 用户ID（-1表示系统调用）
        :param service_name: 服务名称
        :return: JWT令牌字符串
        """
        payload = {
            "userId": user_id,
            "serviceName": service_name,
            "tokenType": "internal",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(milliseconds=InternalTokenUtil._expiration),
        }
        return jwt.encode(payload, InternalTokenUtil._secret, algorithm="HS256")

    def validate_internal_token(self, token: str) -> Dict[str, Any]:
        """
        验证内部服务令牌

        :param token: JWT令牌字符串
        :return: 验证成功返回解密后的声明，失败抛出异常
        """
        try:
            decoded = jwt.decode(token, InternalTokenUtil._secret, algorithms=["HS256"])
            return decoded
        except jwt.ExpiredSignatureError:
            raise BusinessException(Constants.INTERNAL_TOKEN_EXPIRED)
        except jwt.InvalidTokenError:
            raise BusinessException(Constants.INTERNAL_TOKEN_INVALID)

    def extract_user_id(self, token: str) -> Optional[int]:
        """
        从令牌中提取用户ID

        :param token: JWT令牌字符串
        :return: 用户ID
        """
        claims: Dict[str, Any] = self.validate_internal_token(token)
        return claims.get("userId")

    def extract_service_name(self, token: str) -> Optional[str]:
        """
        从令牌中提取服务名称

        :param token: JWT令牌字符串
        :return: 服务名称
        """
        claims: Dict[str, Any] = self.validate_internal_token(token)
        return claims.get("serviceName")
