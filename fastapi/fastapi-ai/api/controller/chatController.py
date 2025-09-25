import datetime
import time
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from common.utils import success,fileLogger
from common.decorators import log
from entity.dto import ChatRequest, ChatResponse, ChatResponseData, AIServiceType
from api.service import CozeService, get_coze_service, GeminiService, get_gemini_service
from common.middleware import get_current_user_id

router: APIRouter = APIRouter(prefix="/chat", tags=["聊天接口"])

@router.post("/send", response_model=ChatResponse)
@log("普通聊天")
async def send_message(
    request: ChatRequest,
    cozeService: CozeService = Depends(get_coze_service),
    geminiService: GeminiService = Depends(get_gemini_service)
) -> JSONResponse:
    """发送聊天消息"""
    try:
        user_id: str = get_current_user_id() or ""
        # 使用实际用户ID替代请求中的user_id
        actual_user_id: str = user_id or "1"
        # 根据请求的服务类型选择对应的AI服务
        if request.service == AIServiceType.GEMINI:
            fileLogger.info(f"使用Gemini服务处理用户 {actual_user_id} 的请求")
            response_message: str = await geminiService.simple_chat(
                message=request.message,
                user_id=actual_user_id
            )
        else:  # 默认使用Coze服务
            fileLogger.info(f"使用Coze服务处理用户 {actual_user_id} 的请求")
            response_message: str = await cozeService.simple_chat(
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
        return success(response_data)
            
    except Exception as e:
        fileLogger.error(f"聊天接口异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"聊天服务异常: {str(e)}")

@router.post("/stream", response_model=ChatResponse)
@log("流式聊天")
async def stream_message(
    request: ChatRequest,
    cozeService: CozeService = Depends(get_coze_service),
    geminiService: GeminiService = Depends(get_gemini_service)
) -> StreamingResponse:
    """流式发送聊天消息"""
    try:
        user_id: str = get_current_user_id() or ""
        actual_user_id: str = user_id or "1"
        conversation_id: str = request.conversation_id or f"{actual_user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        chat_id: str = f"chat_{uuid.uuid4().hex[:12]}"
        
        async def event_generator():
            message_acc = ""
            try:
                # 根据请求的服务类型选择对应的AI服务
                if request.service == AIServiceType.GEMINI:
                    fileLogger.info(f"使用Gemini流式服务处理用户 {actual_user_id} 的请求")
                    stream_generator = await geminiService.stream_chat(
                        message=request.message,
                        user_id=actual_user_id
                    )
                else:  # 默认使用Coze服务
                    fileLogger.info(f"使用Coze流式服务处理用户 {actual_user_id} 的请求")
                    stream_generator = await cozeService.stream_chat(
                        message=request.message,
                        user_id=actual_user_id
                    )
                
                async for chunk in stream_generator:
                    message_acc += chunk
                    data = success({
                            "message": message_acc,
                            "conversation_id": conversation_id,
                            "chat_id": chat_id,
                            "user_id": actual_user_id,
                            "timestamp": int(time.time()),
                            "service": request.service.value
                        })
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            except Exception as e:
                fileLogger.error(f"流式聊天接口异常: {str(e)}")
                data = {
                    "code": 0,
                    "data": None,
                    "msg": f"流式聊天服务异常: {str(e)}"
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        fileLogger.error(f"流式聊天接口异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"流式聊天服务异常: {str(e)}")