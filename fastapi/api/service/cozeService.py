import asyncio
from typing import List, Dict, Any, AsyncGenerator, Optional
from cozepy import Coze, TokenAuth, Message, ChatStatus
from fastapi import Depends
from sqlalchemy.orm import Session
from common.utils.writeLog import fileLogger as logger
from config.config import load_config, load_secret_config
from config.mysql import get_db
from config.mongodb import db as mongo_db
from entity.po.article import Article
from entity.po.user import User
from common.middleware.ContextMiddleware import get_current_user_id, get_current_username


class CozeService:
    api_key: str
    bot_id: str
    base_url: str
    timeout: int
    coze_client: Coze

    def __init__(self) -> None:
        """初始化 Coze 服务"""
        api_key: str = load_secret_config("coze")["api_key"]
        bot_id: str = load_config("coze")["bot_id"]
        base_url: str = load_config("coze")["base_url"]
        timeout: int = load_config("coze")["timeout"]

        self.api_key: str = api_key
        self.bot_id: str = bot_id
        self.base_url: str = base_url
        self.timeout: int = timeout

        self.coze_client: Coze = Coze(
            auth=TokenAuth(token=self.api_key),
            base_url=self.base_url
        )

        logger.info("Coze 服务初始化完成")
    
    async def simple_chat(self, message: str, user_id: str = "default", db: Optional[Session] = None) -> str:
        """简单聊天接口"""
        try:
            prompt: str = self.get_prompt(message, db)
            logger.info(f"用户 {user_id} 发送消息: {prompt}")
            chat: Any = self.coze_client.chat.create(
                bot_id=self.bot_id,
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
    
    async def stream_chat(self, message: str, user_id: str = "default", db: Optional[Session] = None) -> AsyncGenerator[str, None]:
        """流式聊天接口 - 兼容异步调用"""
        try:
            logger.info(f"用户 {user_id} 开始流式聊天: {message}")

            prompt: str = self.get_prompt(message, db)
            logger.info(f"用户 {user_id} 发送消息: {prompt}")
            def sync_stream() -> Any:
                return self.coze_client.chat.stream(
                    bot_id=self.bot_id,
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
                    yield content
        except Exception as e:
            logger.error(f"流式聊天异常: {str(e)}")
            if "4015" in str(e):
                yield "机器人未发布到 API 频道"
            else:
                yield f"流式聊天服务异常: {str(e)}"

    def search_article_from_db(self, db: Session = Depends(get_db)) -> str:
        articles: List[Article] = (
            db.query(Article)
            .order_by(Article.create_at.desc())
            .limit(100)
            .all()
        )
        if not articles:
            return "没有找到相关的知识库内容"
        content_list: List[str] = []
        for article in articles:
            content_list.append(
                f"标题: {article.title}, 内容: {article.content[:100]}, 用户ID: {article.user_id}, 标签: {article.tags}, 状态: {article.status}, 创建时间: {article.create_at.isoformat() if article.create_at else '未知'}, 更新时间: {article.update_at.isoformat() if article.update_at else '未知'}, 浏览量: {article.views}"
            )
        return "\n".join(content_list) if content_list else "没有找到相关的知识库内容"
    
    def search_user_from_db(self, db: Session = Depends(get_db)) -> str:
        users: List[User] = db.query(User).all()
        if not users:
            return "没有找到相关的用户信息"
        user_list: List[str] = []
        for user in users:
            user_list.append(f"ID: {user.id}, 名称: {user.name}, 年龄: {user.age}, 邮箱: {user.email}, 角色: {user.role}")
        return "\n".join(user_list) if user_list else "没有找到相关的用户信息"
    
    def search_logs_from_db(self) -> str:
        logs = mongo_db["articlelogs"]
        cursor: Any = logs.find().sort("createdAt", -1).limit(100)
        log_list: List[str] = []
        for log in cursor:
            log_str: str = ", ".join([f"{k}: {v}" for k, v in log.items()])
            log_list.append(log_str)
        return "\n".join(log_list) if log_list else "没有找到相关的日志信息"
    
    def get_prompt(self, message: str, db: Session = Depends(get_db)) -> str:
        user_id: str = get_current_user_id() or ""
        username: str = get_current_username() or ""
        userInfo: str = f"用户ID: {user_id}, 用户名: {username}"
        article: str = self.search_article_from_db(db)
        user: str = self.search_user_from_db(db)
        logs: str = self.search_logs_from_db()
        knowledge: str = f"当前用户信息(提问的用户，一般会称“我”)：{userInfo}\n文章信息：{article}\n用户信息：{user}\n日志信息：{logs}"
        prompt: str = f"已知信息如下：{knowledge}\n用户提问：{message}"
        return prompt
    
    async def get_chat_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """获取聊天历史"""
        try:
            try:
                messages = self.coze_client.chat.message.list(
                    conversation_id=conversation_id
                )
            except AttributeError:
                try:
                    messages = self.coze_client.conversations.messages.list(
                        conversation_id=conversation_id
                    )
                except AttributeError:
                    try:
                        messages = self.coze_client.messages.list(
                            conversation_id=conversation_id
                        )
                    except AttributeError:
                        logger.error("无法找到正确的消息历史 API")
                        return []
            history: List[Dict[str, Any]] = []
            message_list = messages.data if hasattr(messages, 'data') else messages
            for msg in message_list:
                history.append({
                    "id": getattr(msg, 'id', ''),
                    "role": getattr(msg, 'role', ''),
                    "content": getattr(msg, 'content', ''),
                    "type": getattr(msg, 'type', ''),
                    "created_at": getattr(msg, 'created_at', 0)
                })
            return history
        except Exception as e:
            logger.error(f"获取聊天历史异常: {str(e)}")
            return []
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            workspaces = self.coze_client.workspaces.list()
            return len(workspaces.data) >= 0
        except Exception as e:
            logger.error(f"Coze 健康检查失败: {str(e)}")
            return False
    
    def get_bot_info(self) -> Dict[str, Any]:
        """获取机器人信息"""
        try:
            bot = self.coze_client.bots.retrieve(bot_id=self.bot_id)
            return {
                "bot_id": bot.bot_id,
                "name": getattr(bot, 'name', 'Unknown'),
                "description": getattr(bot, 'description', 'No description'),
                "status": "active"
            }
        except Exception as e:
            logger.error(f"获取机器人信息失败: {str(e)}")
            return {"error": str(e)}
    
    def check_api_structure(self) -> Dict[str, Any]:
        """检查 API 结构 - 调试用"""
        try:
            structure_info: Dict[str, Any] = {
                "chat_client_methods": [],
                "available_apis": []
            }
            if hasattr(self.coze_client, 'chat'):
                chat_methods: List[str] = [method for method in dir(self.coze_client.chat) if not method.startswith('_')]
                structure_info["chat_client_methods"] = chat_methods
                if hasattr(self.coze_client.chat, 'message'):
                    message_methods: List[str] = [method for method in dir(self.coze_client.chat.message) if not method.startswith('_')]
                    structure_info["chat_message_methods"] = message_methods
            client_attrs: List[str] = [attr for attr in dir(self.coze_client) if not attr.startswith('_')]
            structure_info["available_apis"] = client_attrs
            return structure_info
        except Exception as e:
            return {"error": str(e)}


try:
    coze_service: Optional[CozeService] = CozeService()
    logger.info("Coze 服务全局实例创建成功")
    api_structure: Dict[str, Any] = coze_service.check_api_structure()
    logger.info(f"Coze API 结构: {api_structure}")
except Exception as e:
    logger.error(f"Coze 服务初始化失败: {str(e)}")
    coze_service: Optional[CozeService] = None
