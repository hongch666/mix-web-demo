import datetime
import json
import time
import uuid
from typing import Any, AsyncGenerator, Dict
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlmodel import Session
from starlette.concurrency import run_in_threadpool
from api.service import (
    GeminiService, get_gemini_service, 
    QwenService, get_qwen_service, 
    DoubaoService, get_doubao_service, 
    AiHistoryService, get_ai_history_service
)
from common.utils import success, fileLogger as logger
from common.exceptions import BusinessException
from common.decorators import log, requireInternalToken
from common.middleware import get_current_user_id
from common.config import get_db
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
@requireInternalToken
async def send_message(
    _: Request,
    request: ChatRequest,
    db: Session = Depends(get_db),
    geminiService: GeminiService = Depends(get_gemini_service),
    qwenService: QwenService = Depends(get_qwen_service),
    doubaoService: DoubaoService = Depends(get_doubao_service),
    aiHistoryService: AiHistoryService = Depends(get_ai_history_service)
) -> JSONResponse:
    """发送聊天消息"""
    
    user_id: str = get_current_user_id() or ""
    # 使用实际用户ID替代请求中的user_id
    actual_user_id: str = user_id or "1"
    
    try:
        # 根据请求的服务类型选择对应的AI服务
        if request.service == AIServiceType.GEMINI:
            logger.info(f"使用Gemini服务处理用户 {actual_user_id} 的请求")
            response_message: str = await geminiService.simple_chat(
                message=request.message,
                user_id=actual_user_id,
                db=db
            )
        elif request.service == AIServiceType.QWEN:
            logger.info(f"使用Qwen服务处理用户 {actual_user_id} 的请求")
            response_message: str = await qwenService.simple_chat(
                message=request.message,
                user_id=actual_user_id,
                db=db
            )
        else:  # 默认使用豆包服务
            logger.info(f"使用豆包服务处理用户 {actual_user_id} 的请求")
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
            await run_in_threadpool(aiHistoryService.create_ai_history, history, db)
            logger.info(f"AI历史记录已保存: user_id={actual_user_id}, ai_type={request.service.value}")
        except Exception as history_error:
            logger.error(f"保存AI历史记录失败: {str(history_error)}")
        
        # 成功响应 - 按照success格式
        response_data: ChatResponseData = ChatResponseData(
            message=response_message,
            conversation_id=conversation_id,
            chat_id=chat_id,
            user_id=actual_user_id,
            timestamp=int(time.time())
        )
        return success(response_data)

    except BusinessException:
        # 业务异常直接重新抛出，不记录耗时
        raise
    except Exception as e:
        logger.error(f"聊天接口异常: {str(e)}", exc_info=True)
        return ChatResponse(
            code=0,
            data=None,
            msg=f"聊天服务异常: {str(e)}"
        )

@router.post(
    "/stream",
    response_model=ChatResponse,
    summary="流式聊天",
    description="流式发送聊天消息并返回响应"
)
@log("流式聊天")
async def stream_message(
    _: Request,
    request: ChatRequest,
    geminiService: GeminiService = Depends(get_gemini_service),
    qwenService: QwenService = Depends(get_qwen_service),
    doubaoService: DoubaoService = Depends(get_doubao_service),
    aiHistoryService: AiHistoryService = Depends(get_ai_history_service)
) -> StreamingResponse:
    """流式发送聊天消息"""
    
    user_id: str = get_current_user_id() or ""
    actual_user_id: str = user_id or "1"
    conversation_id: str = request.conversation_id or f"{actual_user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    chat_id: str = f"chat_{uuid.uuid4().hex[:12]}"
    
    async def event_generator() -> AsyncGenerator[str, None]:
        message_acc: str = ""
        thinking_acc: str = ""
        # 在 event_generator 内部创建 db session，确保流式处理完成后立即释放
        db_gen = get_db()
        db: Session = next(db_gen)
        
        try:
            # 根据请求的服务类型选择对应的AI服务
            if request.service == AIServiceType.GEMINI:
                logger.info(f"使用Gemini流式服务处理用户 {actual_user_id} 的请求")
                stream_generator: AsyncGenerator[Any, None] = geminiService.stream_chat(
                    message=request.message,
                    user_id=actual_user_id,
                    db=db
                )
            elif request.service == AIServiceType.QWEN:
                logger.info(f"使用Qwen流式服务处理用户 {actual_user_id} 的请求")
                stream_generator = qwenService.stream_chat(
                    message=request.message,
                    user_id=actual_user_id,
                    db=db
                )
            else:  # 默认使用豆包服务
                logger.info(f"使用豆包流式服务处理用户 {actual_user_id} 的请求")
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
                
                # 记录chunk长度（用于调试）
                logger.debug(f"流式块类型: {chunk_type}, 块内容长度: {len(chunk_content)}")
                
                # 分别累积思考过程和最终内容
                if chunk_type == "thinking":
                    thinking_acc += chunk_content
                elif chunk_type == "content":
                    message_acc += chunk_content
                
                # 构建响应数据 - 确保chunk_content完整输出
                data: Dict[str, Any] = success({
                    "message": message_acc,
                    "conversation_id": conversation_id,
                    "chat_id": chat_id,
                    "user_id": actual_user_id,
                    "timestamp": int(time.time()),
                    "service": request.service.value,
                    "message_type": chunk_type,
                    "chunk": chunk_content  # 保证完整的chunk内容
                })
                # 使用 ensure_ascii=False 保证 UTF-8 编码，avoid_json_tricks 保证完整性
                json_str: str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
                logger.debug(f"SSE 数据包大小: {len(json_str)} 字节")
                yield f"data: {json_str}\n\n"
            
            # 流式聊天完成后保存AI历史记录（在完成流式传输后）
            if message_acc:
                try:
                    history = AiHistory(
                        user_id=int(actual_user_id),
                        ask=request.message,
                        reply=message_acc,
                        thinking=thinking_acc if thinking_acc else None,
                        ai_type=request.service.value
                    )
                    await run_in_threadpool(aiHistoryService.create_ai_history, history, db)
                    logger.info(f"流式AI历史记录已保存: user_id={actual_user_id}, ai_type={request.service.value}")
                except Exception as history_error:
                    logger.error(f"保存流式AI历史记录失败: {str(history_error)}")

        except BusinessException:
            # 业务异常直接重新抛出，不记录耗时
            raise
        except Exception as e:
            logger.error(f"流式聊天接口异常: {str(e)}")
            data = {
                "code": 0,
                "data": None,
                "msg": f"流式聊天服务异常: {str(e)}"
            }
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
        finally:
            # 确保 session 被正确关闭，释放数据库连接
            if db:
                db.close()
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")