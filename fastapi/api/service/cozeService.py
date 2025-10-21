import asyncio
from functools import lru_cache
from typing import Any, AsyncGenerator, Optional
from cozepy import Coze, TokenAuth, Message, ChatStatus
from fastapi import Depends
from sqlmodel import Session
from api.service import PromptService, get_prompt_service
from common.utils import fileLogger as logger
from config import load_config, load_secret_config


class CozeService:
    def __init__(self,promptService: PromptService):
        self.promptService = promptService
        # 把 Coze 客户端的配置和初始化放到实例内，避免模块导入时执行网络初始化
        try:
            coze_cfg = load_config("coze") or {}
            coze_secret = load_secret_config("coze") or {}
            self._api_key: str = coze_secret.get("api_key")
            self._bot_id: str = coze_cfg.get("bot_id")
            self._base_url: str = coze_cfg.get("base_url")
            self._timeout: int = coze_cfg.get("timeout")
            if self._api_key and self._base_url:
                self.coze_client: Coze = Coze(auth=TokenAuth(token=self._api_key), base_url=self._base_url)
                logger.info("Coze 服务初始化完成 (实例化)")
            else:
                self.coze_client = None
                logger.warning("Coze 配置不完整，客户端未初始化")
        except Exception as e:
            self.coze_client = None
            logger.error(f"初始化 Coze 客户端失败: {e}")

    async def simple_chat(self,message: str, user_id: str = "default", db: Optional[Session] = None) -> str:
            """简单聊天接口"""
            try:
                prompt: str = self.promptService.get_prompt(message, db)
                logger.info(f"用户 {user_id} 发送消息: {prompt}")
                if not getattr(self, 'coze_client', None):
                    return "聊天服务未配置或初始化失败"
                chat: Any = self.coze_client.chat.create(
                    bot_id=self._bot_id,
                    user_id=user_id,
                    additional_messages=[
                        Message.build_user_question_text(content=prompt)
                    ]
                )
                logger.info(f"创建聊天会话: {chat.id}")
                max_attempts: int = 60
                attempt: int = 0
                while attempt < max_attempts:
                    try:
                        chat_poll: Any = self.coze_client.chat.retrieve(
                            chat_id=chat.id,
                            conversation_id=chat.conversation_id
                        )
                        logger.info(f"聊天状态: {chat_poll.status}")
                        if chat_poll.status == ChatStatus.COMPLETED:
                            try:
                                messages: Any = self.coze_client.chat.message.list(
                                    chat_id=chat.id,
                                    conversation_id=chat.conversation_id
                                )
                            except AttributeError:
                                try:
                                    messages: Any = self.coze_client.conversations.messages.list(
                                        conversation_id=chat.conversation_id
                                    )
                                except AttributeError:
                                    try:
                                        messages: Any = self.coze_client.messages.list(
                                            chat_id=chat.id,
                                            conversation_id=chat.conversation_id
                                        )
                                    except AttributeError:
                                        logger.error("无法找到正确的消息列表 API")
                                        return "API 调用方式不匹配，请检查 cozepy 库版本"
                            if hasattr(messages, 'data'):
                                for msg in messages.data:
                                    if msg.role == "assistant" and msg.type == "answer":
                                        response: str = msg.content
                                        logger.info(f"Coze 回复长度: {len(response)} 字符")
                                        return response
                            else:
                                for msg in messages:
                                    if hasattr(msg, 'role') and msg.role == "assistant":
                                        response: str = getattr(msg, 'content', '')
                                        if response:
                                            logger.info(f"Coze 回复长度: {len(response)} 字符")
                                            return response
                            return "抱歉，没有收到回复"
                        elif chat_poll.status == ChatStatus.FAILED:
                            logger.error("Coze 聊天失败")
                            return "聊天处理失败，请稍后重试"
                        elif chat_poll.status == ChatStatus.REQUIRES_ACTION:
                            logger.warning("聊天需要用户操作")
                            return "聊天需要额外操作，请检查机器人配置"
                        await asyncio.sleep(1)
                        attempt += 1
                    except Exception as poll_error:
                        logger.error(f"轮询聊天状态异常: {str(poll_error)}")
                        await asyncio.sleep(2)
                        attempt += 1
                logger.warning(f"聊天超时，已等待 {max_attempts} 秒")
                return "聊天响应超时，请稍后重试"
            except Exception as e:
                logger.error(f"Coze 聊天异常: {str(e)}")
                if "4015" in str(e) or "not been published" in str(e):
                    return "机器人未发布到 API 频道。请在 Coze 平台将机器人发布到 'Agent As API' 频道。"
                return f"聊天服务异常: {str(e)}"
        
    async def stream_chat(self,message: str, user_id: str = "default", db: Optional[Session] = None) -> AsyncGenerator[str, None]:
            """流式聊天接口 - 兼容异步调用"""
            try:
                logger.info(f"用户 {user_id} 开始流式聊天: {message}")

                prompt: str = self.promptService.get_prompt(message, db)
                logger.info(f"用户 {user_id} 发送消息: {prompt}")
                if not getattr(self, 'coze_client', None):
                    yield "聊天服务未配置或初始化失败"
                    return
                def sync_stream() -> Any:
                    return self.coze_client.chat.stream(
                        bot_id=self._bot_id,
                        user_id=user_id,
                        additional_messages=[
                            Message.build_user_question_text(content=prompt)
                        ]
                    )

                loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
                chat_stream: Any = await loop.run_in_executor(None, sync_stream)

                for event in chat_stream:
                    logger.info(f"收到流事件: {event}")
                    content: Optional[str] = None
                    if hasattr(event, 'event'):
                        if event.event == "conversation.message.delta" or event.event == "conversation.message.completed":
                            if hasattr(event, 'message') and hasattr(event.message, 'content'):
                                content = event.message.content
                    if not content and hasattr(event, 'data') and hasattr(event.data, 'content'):
                        content = event.data.content
                    if not content and hasattr(event, 'content'):
                        content = event.content
                    if content is not None:
                        current_length = len(content)
                        # 检测内容长度是否超过固定阈值（超过10字符视为异常增长）
                        if current_length > 10:
                            logger.info(f"检测到内容长度过长: {current_length} 字符，跳过此内容")
                            continue
                        yield content
            except Exception as e:
                logger.error(f"流式聊天异常: {str(e)}")
                if "4015" in str(e):
                    yield "机器人未发布到 API 频道"
                else:
                    yield f"流式聊天服务异常: {str(e)}"

    

@lru_cache()
def get_coze_service(promptService: PromptService = Depends(get_prompt_service)) -> CozeService:
    return CozeService(promptService)