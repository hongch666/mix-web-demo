from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError

from app.core.constants import HttpCode

from .alias import Alias


class AIServiceType(StrEnum):
    """AI服务类型枚举"""

    GPT = "GPT"
    GEMINI = "Gemini"
    GLM = "GLM"


class StreamFormat(StrEnum):
    """流式响应帧格式枚举"""

    # 项目自定义帧，包含累计 message、chunk 与 message_type，前端契约
    NATIVE = "native"
    # OpenAI Chat Completions 兼容分片，思考走 delta.reasoning_content，正文走 delta.content
    OPENAI = "openai"


class ChatRequest(BaseModel):
    """聊天请求模型"""

    model_config = {"populate_by_name": True}

    message: str = Field(..., description="用户消息")
    userId: Optional[str] = Alias("userId", default="default", description="用户ID")
    conversationId: Optional[str] = Alias(
        "conversationId", default=None, description="会话ID"
    )
    service: AIServiceType = Field(
        default=AIServiceType.GPT, description="AI服务类型：gpt、gemini或glm"
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
            AIServiceType.GLM.value,
        }
        if isinstance(value, AIServiceType):
            return value
        if not isinstance(value, str) or value not in allowed_values:
            raise PydanticCustomError(
                "service_invalid",
                "AI服务类型必须是gpt、gemini或glm",
            )
        return value


class ChatStreamRequest(ChatRequest):
    """流式聊天请求模型

    streamFormat 可选，缺省为 native，保持前端既有契约不变
    """

    streamFormat: StreamFormat = Field(
        default=StreamFormat.NATIVE,
        description=(
            "流式响应帧格式：native 为项目自定义帧（message/chunk/message_type，前端使用），"
            "openai 为 OpenAI Chat Completions 兼容分片（思考走 delta.reasoning_content，"
            "正文走 delta.content，末尾返回 [DONE]），便于 Apifox 等标准客户端自动合并"
        ),
    )


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


class OpenAIStreamDelta(BaseModel):
    """OpenAI 兼容流式分片的增量内容"""

    role: Optional[str] = Field(default=None, description="首帧声明的 assistant 角色")
    content: Optional[str] = Field(default=None, description="当前帧的正文增量")
    reasoning_content: Optional[str] = Field(
        default=None, description="当前帧的思考过程增量"
    )


class OpenAIStreamChoice(BaseModel):
    """OpenAI 兼容流式分片中的单个选项"""

    index: int = Field(default=0, description="选项序号")
    delta: OpenAIStreamDelta = Field(description="当前帧的增量内容")
    finish_reason: Optional[str] = Field(
        default=None, description="结束原因，结束帧为 stop，其余帧为空"
    )


class OpenAIStreamChunk(BaseModel):
    """streamFormat=openai 时的单条 SSE JSON 分片"""

    id: str = Field(description="本次补全 ID")
    object: str = Field(
        default="chat.completion.chunk", description="OpenAI 流式分片对象类型"
    )
    created: int = Field(description="分片创建时间戳")
    model: str = Field(description="实际使用的模型名称")
    conversation_id: str = Field(description="会话 ID")
    chat_id: str = Field(description="本次聊天 ID")
    choices: list[OpenAIStreamChoice] = Field(description="流式选项列表")
