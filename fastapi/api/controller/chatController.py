import datetime
import time
import uuid
from fastapi import APIRouter, HTTPException

from entity.dto.chatDTO import ChatRequest, ChatResponse, ChatResponseData
from api.service.cozeService import coze_service
from common.utils.writeLog import fileLogger
from common.middleware.ContextMiddleware import get_current_user_id, get_current_username

router: APIRouter = APIRouter(prefix="/chat", tags=["聊天接口"])

@router.post("/send", response_model=ChatResponse)
async def send_message(
    request: ChatRequest
) -> ChatResponse:
    """发送聊天消息"""
    try:
        user_id: str = get_current_user_id() or ""
        username: str = get_current_username() or ""
        fileLogger.info("用户" + user_id + ":" + username + " POST /generate/tags: 生成tags\nChatRequest: " + request.json())
        # 使用实际用户ID替代请求中的user_id
        actual_user_id: str = user_id or request.user_id
        # 普通响应
        response_message: str = await coze_service.simple_chat(
            message=request.message,
            user_id=actual_user_id
        )
        
        # 生成会话ID（如果没有提供）
        conversation_id: str = request.conversation_id or f"{actual_user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        chat_id: str = f"chat_{uuid.uuid4().hex[:12]}"
        
        # 检查是否有错误
        if "异常" in response_message or "错误" in response_message or "失败" in response_message:
            return ChatResponse(
                code=0,
                data=None,
                msg=response_message
            )
        
        # 成功响应 - 按照success格式
        response_data: ChatResponseData = ChatResponseData(
            message=response_message,
            conversation_id=conversation_id,
            chat_id=chat_id,
            user_id=actual_user_id,
            timestamp=int(time.time())
        )
        
        return ChatResponse(
            code=1,
            data=response_data,
            msg="success"
        )
            
    except Exception as e:
        fileLogger.error(f"聊天接口异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"聊天服务异常: {str(e)}")