import asyncio
from typing import List, Dict, Any, AsyncGenerator, Optional
from cozepy import Coze, TokenAuth, Message, ChatStatus
from fastapi import Depends
from sqlalchemy.orm import Session
from api.mapper import get_all_articlelogs_limit_mapper,get_all_subcategories_mapper,get_article_limit_mapper,get_all_users_mapper,get_all_categories_mapper
from common.utils import fileLogger as logger
from config import load_config, load_secret_config,get_db
from entity.po import Article,User,SubCategory
from common.middleware import get_current_user_id, get_current_username


# 全局coze配置
_api_key: str = load_secret_config("coze")["api_key"]
_bot_id: str = load_config("coze")["bot_id"]
_base_url: str = load_config("coze")["base_url"]
_timeout: int = load_config("coze")["timeout"]
coze_client: Coze = Coze(auth=TokenAuth(token=_api_key), base_url=_base_url)
logger.info("Coze 服务初始化完成")
    
async def simple_chat(message: str, user_id: str = "default", db: Optional[Session] = None) -> str:
        """简单聊天接口"""
        try:
            prompt: str = get_prompt(message, db)
            logger.info(f"用户 {user_id} 发送消息: {prompt}")
            chat: Any = coze_client.chat.create(
                bot_id=_bot_id,
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
                    chat_poll: Any = coze_client.chat.retrieve(
                        chat_id=chat.id,
                        conversation_id=chat.conversation_id
                    )
                    logger.info(f"聊天状态: {chat_poll.status}")
                    if chat_poll.status == ChatStatus.COMPLETED:
                        try:
                            messages: Any = coze_client.chat.message.list(
                                chat_id=chat.id,
                                conversation_id=chat.conversation_id
                            )
                        except AttributeError:
                            try:
                                messages: Any = coze_client.conversations.messages.list(
                                    conversation_id=chat.conversation_id
                                )
                            except AttributeError:
                                try:
                                    messages: Any = coze_client.messages.list(
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
    
async def stream_chat(message: str, user_id: str = "default", db: Optional[Session] = None) -> AsyncGenerator[str, None]:
        """流式聊天接口 - 兼容异步调用"""
        try:
            logger.info(f"用户 {user_id} 开始流式聊天: {message}")

            prompt: str = get_prompt(message, db)
            logger.info(f"用户 {user_id} 发送消息: {prompt}")
            def sync_stream() -> Any:
                return coze_client.chat.stream(
                    bot_id=_bot_id,
                    user_id=user_id,
                    additional_messages=[
                        Message.build_user_question_text(content=prompt)
                    ]
                )

            loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
            chat_stream: Any = await loop.run_in_executor(None, sync_stream)

            previous_length = 0
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
                    # 检测内容长度是否翻倍增长（视为异常增长）
                    if previous_length > 10 and current_length >= previous_length * 1.5:
                        logger.info(f"检测到内容长度异常增长: {previous_length} -> {current_length}，跳过此内容")
                        continue
                    previous_length = current_length
                    yield content
        except Exception as e:
            logger.error(f"流式聊天异常: {str(e)}")
            if "4015" in str(e):
                yield "机器人未发布到 API 频道"
            else:
                yield f"流式聊天服务异常: {str(e)}"

def search_article_from_db(db: Session = Depends(get_db)) -> str:
        articles: List[Article] = get_article_limit_mapper(db)
        if not articles:
            return "没有找到相关的知识库内容"
        content_list: List[str] = []
        for article in articles:
            content_list.append(
                f"标题: {article.title}, 内容: {article.content[:100]}, 用户ID: {article.user_id}, 标签: {article.tags}, 状态: {article.status}, 创建时间: {article.create_at.isoformat() if article.create_at else '未知'}, 更新时间: {article.update_at.isoformat() if article.update_at else '未知'}, 浏览量: {article.views}"
            )
        return "\n".join(content_list) if content_list else "没有找到相关的知识库内容"
    
def search_user_from_db(db: Session = Depends(get_db)) -> str:
        users: List[User] = get_all_users_mapper(db)
        if not users:
            return "没有找到相关的用户信息"
        user_list: List[str] = []
        for user in users:
            user_list.append(f"ID: {user.id}, 名称: {user.name}, 年龄: {user.age}, 邮箱: {user.email}, 角色: {user.role}")
        return "\n".join(user_list) if user_list else "没有找到相关的用户信息"
    
def search_category_from_db(db: Session = Depends(get_db)) -> str:
        categories: List[Dict[str, Any]] = get_all_categories_mapper(db)
        if not categories:
            return "没有找到相关的分类信息"
        category_list: List[str] = []
        for category in categories:
            category_list.append(f"分类ID: {category.id}, 名称: {category.name}")
        return "\n".join(category_list) if category_list else "没有找到相关的分类信息"
    
def search_sub_category_from_db(db: Session = Depends(get_db)) -> str:
        sub_categories: List[SubCategory] = get_all_subcategories_mapper(db)
        if not sub_categories:
            return "没有找到相关的子分类信息"
        sub_category_list: List[str] = []
        for sub_category in sub_categories:
            sub_category_list.append(f"子分类ID: {sub_category.id}, 名称: {sub_category.name}, 所属分类ID: {sub_category.category_id}")
        return "\n".join(sub_category_list) if sub_category_list else "没有找到相关的子分类信息"
    
def search_logs_from_db() -> str:
        cursor: Any = get_all_articlelogs_limit_mapper()
        log_list: List[str] = []
        for log in cursor:
            log_str: str = ", ".join([f"{k}: {v}" for k, v in log.items()])
            log_list.append(log_str)
        return "\n".join(log_list) if log_list else "没有找到相关的日志信息"
    
def get_prompt(message: str, db: Session = Depends(get_db)) -> str:
        user_id: str = get_current_user_id() or ""
        username: str = get_current_username() or ""
        userInfo: str = f"用户ID: {user_id}, 用户名: {username}"
        article: str = search_article_from_db(db)
        user: str = search_user_from_db(db)
        category: str = search_category_from_db(db)
        sub_category: str = search_sub_category_from_db(db)
        logs: str = search_logs_from_db()
        knowledge: str = (f"当前用户信息(提问的用户，一般会称“我”)：{userInfo}\n文章信息：{article}\n用户信息：{user}\n分类信息：{category}\n日志信息：{logs}"
        f"\n子分类信息：{sub_category}")
        prompt: str = f"已知信息如下：{knowledge}\n用户提问：{message}"
        return prompt