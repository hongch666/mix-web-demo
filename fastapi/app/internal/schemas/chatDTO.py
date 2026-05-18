from enum import Enum
from typing import Optional

from app.core.base import HttpCode
from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError

from .alias import Alias


class AIServiceType(str, Enum):
    """AI服务类型枚举"""

    GPT = "GPT"
    GEMINI = "Gemini"
    DEEPSEEK = "DeepSeek"


class ChatRequest(BaseModel):
    """聊天请求模型"""
    model_config = {"populate_by_name": True}

    message: str = Field(..., description="用户消息")
    userId: Optional[str] = Alias("userId", default="default", description="用户ID")
    conversationId: Optional[str] = Alias(
        "conversationId", default=None, description="会话ID"
    )
    service: AIServiceType = Field(
        default=AIServiceType.GPT, description="AI服务类型：gpt、gemini或deepseek"
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        if not value.strip():
            raise PydanticCustomError("message_empty", "用户消息不能为空")
        return value

    @field_validator("service", mode="before")
    @classmethod
    def validate_service(cls, value: object) -> object:
        allowed_values = {
            AIServiceType.GPT.value,
            AIServiceType.GEMINI.value,
            AIServiceType.DEEPSEEK.value,
        }
        if isinstance(value, AIServiceType):
            return value
        if not isinstance(value, str) or value not in allowed_values:
            raise PydanticCustomError(
                "service_invalid",
                "AI服务类型必须是gpt、gemini或deepseek",
            )
        return value


class ChatResponseData(BaseModel):
    """聊天响应数据模型 - 内部数据结构"""
    model_config = {"populate_by_name": True}

    message: str = Field(..., description="回复消息")
    conversationId: Optional[str] = Alias(
        "conversationId", default=None, description="会话ID"
    )
    chatId: Optional[str] = Alias("chatId", default=None, description="聊天ID")
    userId: Optional[str] = Alias("userId", default=None, description="用户ID")
    timestamp: Optional[int] = Field(default=None, description="时间戳")


class ChatResponse(BaseModel):
    """聊天响应模型 - 符合success()格式"""

    code: int = Field(default=HttpCode.OK, description="响应码：3位HTTP状态码")
    data: Optional[ChatResponseData] = Field(default=None, description="响应数据")
    msg: str = Field(default="success", description="响应消息")
