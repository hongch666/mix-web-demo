from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class AIServiceType(str, Enum):
    """AI服务类型枚举"""
    COZE = "coze"
    GEMINI = "gemini"
    TONGYI = "tongyi"

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., description="用户消息", min_length=1, max_length=4000)
    user_id: Optional[str] = Field(default="default", description="用户ID")
    conversation_id: Optional[str] = Field(default=None, description="会话ID")
    service: AIServiceType = Field(default=AIServiceType.COZE, description="AI服务类型：coze、gemini或tongyi")
    # stream: Optional[bool] = Field(default=False, description="是否流式响应")

class ChatResponseData(BaseModel):
    """聊天响应数据模型 - 内部数据结构"""
    message: str = Field(..., description="回复消息")
    conversation_id: Optional[str] = Field(default=None, description="会话ID")
    chat_id: Optional[str] = Field(default=None, description="聊天ID")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    timestamp: Optional[int] = Field(default=None, description="时间戳")

class ChatResponse(BaseModel):
    """聊天响应模型 - 符合success()格式"""
    code: int = Field(default=1, description="响应码：1成功，0失败")
    data: Optional[ChatResponseData] = Field(default=None, description="响应数据")
    msg: str = Field(default="success", description="响应消息")

class ChatHistoryRequest(BaseModel):
    """聊天历史请求模型"""
    conversation_id: str = Field(..., description="会话ID")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    limit: Optional[int] = Field(default=50, description="限制数量")

class ChatMessage(BaseModel):
    """聊天消息模型"""
    id: str = Field(..., description="消息ID")
    role: str = Field(..., description="角色")
    content: str = Field(..., description="内容")
    type: str = Field(..., description="类型")
    created_at: int = Field(..., description="创建时间")