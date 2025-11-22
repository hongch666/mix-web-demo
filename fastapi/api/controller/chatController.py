import datetime
import time
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlmodel import Session
from api.service import GeminiService, get_gemini_service, TongyiService, get_tongyi_service, DoubaoService, get_doubao_service, AiHistoryService, get_ai_history_service
from common.utils import success, fileLogger
from common.decorators import log
from common.middleware import get_current_user_id
from config import get_db
from entity.dto import ChatRequest, ChatResponse, ChatResponseData, AIServiceType
from entity.po import AiHistory

router: APIRouter = APIRouter(prefix="/chat", tags=["AI聊天接口"])

@router.post(
    "/send",
    response_model=ChatResponse,
    summary="普通聊天",
    description="发送聊天消息并返回响应"
)
@log("普通聊天")
async def send_message(
    httpRequest: Request,
    request: ChatRequest,
    db:Session = Depends(get_db),
    geminiService: GeminiService = Depends(get_gemini_service),
    tongyiService: TongyiService = Depends(get_tongyi_service),
    doubaoService: DoubaoService = Depends(get_doubao_service),
    aiHistoryService: AiHistoryService = Depends(get_ai_history_service)
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
                user_id=actual_user_id,
                db=db
            )
        elif request.service == AIServiceType.TONGYI:
            fileLogger.info(f"使用通义千问服务处理用户 {actual_user_id} 的请求")
            response_message: str = await tongyiService.simple_chat(
                message=request.message,
                user_id=actual_user_id,
                db=db
            )
        else:  # 默认使用豆包服务
            fileLogger.info(f"使用豆包服务处理用户 {actual_user_id} 的请求")
            response_message: str = await doubaoService.simple_chat(
                message=request.message,
                user_id=actual_user_id,
                db=db
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
        
        # 保存AI历史记录
        try:
            history = AiHistory(
                user_id=int(actual_user_id),
                ask=request.message,
                reply=response_message,
                thinking=None,
                ai_type=request.service.value
            )
            aiHistoryService.create_ai_history(history, db)
            fileLogger.info(f"AI历史记录已保存: user_id={actual_user_id}, ai_type={request.service.value}")
        except Exception as history_error:
            fileLogger.error(f"保存AI历史记录失败: {str(history_error)}")
        
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

@router.post(
    "/stream",
    response_model=ChatResponse,
    summary="流式聊天",
    description="流式发送聊天消息并返回响应"
)
@log("流式聊天")
async def stream_message(
    httpRequest: Request,
    request: ChatRequest,
    db: Session = Depends(get_db),
    geminiService: GeminiService = Depends(get_gemini_service),
    tongyiService: TongyiService = Depends(get_tongyi_service),
    doubaoService: DoubaoService = Depends(get_doubao_service),
    aiHistoryService: AiHistoryService = Depends(get_ai_history_service)
) -> StreamingResponse:
    """流式发送聊天消息"""
    try:
        user_id: str = get_current_user_id() or ""
        actual_user_id: str = user_id or "1"
        conversation_id: str = request.conversation_id or f"{actual_user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        chat_id: str = f"chat_{uuid.uuid4().hex[:12]}"
        
        async def event_generator():
            message_acc = ""
            thinking_acc = ""
            try:
                # 根据请求的服务类型选择对应的AI服务
                if request.service == AIServiceType.GEMINI:
                    fileLogger.info(f"使用Gemini流式服务处理用户 {actual_user_id} 的请求")
                    stream_generator = geminiService.stream_chat(
                        message=request.message,
                        user_id=actual_user_id,
                        db=db
                    )
                elif request.service == AIServiceType.TONGYI:
                    fileLogger.info(f"使用通义千问流式服务处理用户 {actual_user_id} 的请求")
                    stream_generator = tongyiService.stream_chat(
                        message=request.message,
                        user_id=actual_user_id,
                        db=db
                    )
                else:  # 默认使用豆包服务
                    fileLogger.info(f"使用豆包流式服务处理用户 {actual_user_id} 的请求")
                    stream_generator = doubaoService.stream_chat(
                        message=request.message,
                        user_id=actual_user_id,
                        db=db
                    )
                
                async for chunk in stream_generator:
                    # 解析流式数据块中的消息类型
                    # 格式: {"type": "thinking|content|error", "content": "..."}
                    if isinstance(chunk, dict):
                        chunk_type = chunk.get("type", "content")
                        chunk_content = chunk.get("content", "")
                    else:
                        # 如果是字符串，默认为 content 类型
                        chunk_type = "content"
                        chunk_content = str(chunk)
                    
                    # 分别累积思考过程和最终内容
                    if chunk_type == "thinking":
                        thinking_acc += chunk_content
                    elif chunk_type == "content":
                        message_acc += chunk_content
                    
                    # 构建响应数据
                    data = success({
                        "message": message_acc,
                        "conversation_id": conversation_id,
                        "chat_id": chat_id,
                        "user_id": actual_user_id,
                        "timestamp": int(time.time()),
                        "service": request.service.value,
                        "message_type": chunk_type,
                        "chunk": chunk_content
                    })
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                
                # 流式聊天完成后保存AI历史记录
                if message_acc:
                    try:
                        history = AiHistory(
                            user_id=int(actual_user_id),
                            ask=request.message,
                            reply=message_acc,
                            thinking=thinking_acc if thinking_acc else None,
                            ai_type=request.service.value
                        )
                        aiHistoryService.create_ai_history(history, db)
                        fileLogger.info(f"流式AI历史记录已保存: user_id={actual_user_id}, ai_type={request.service.value}")
                    except Exception as history_error:
                        fileLogger.error(f"保存流式AI历史记录失败: {str(history_error)}")
                        
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