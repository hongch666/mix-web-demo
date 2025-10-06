import asyncio
from functools import lru_cache
from typing import List, Dict, Any, AsyncGenerator, Optional
from cozepy import Coze, TokenAuth, Message, ChatStatus
from fastapi import Depends
from sqlmodel import Session
from api.mapper import ArticleMapper,get_article_mapper,UserMapper,get_user_mapper,ArticleLogMapper,get_articlelog_mapper,SubCategoryMapper,get_subcategory_mapper,CategoryMapper,get_category_mapper,AiHistoryMapper,get_ai_history_mapper,VectorMapper, get_vector_mapper
from api.service import EmbeddingService, get_embedding_service
from common.utils import fileLogger as logger
from config import load_config, load_secret_config,get_db
from config.postgres import get_pg_db
from entity.po import Article,User,SubCategory
from common.middleware import get_current_user_id, get_current_username
from datetime import datetime


class CozeService:
    def __init__(self,articleMapper: ArticleMapper,userMapper: UserMapper,articleLogMapper: ArticleLogMapper,subCategoryMapper: SubCategoryMapper,categoryMapper: CategoryMapper,aiHistoryMapper: AiHistoryMapper):
        self.articleMapper = articleMapper
        self.userMapper = userMapper
        self.articleLogMapper = articleLogMapper
        self.subCategoryMapper = subCategoryMapper
        self.categoryMapper = categoryMapper
        self.aiHistoryMapper = aiHistoryMapper
        try:
            self.vectorMapper: Optional[VectorMapper] = get_vector_mapper()
        except Exception as e:
            self.vectorMapper = None
            logger.warning(f"VectorMapper 初始化失败，向量检索不可用: {e}")
        try:
            self.embeddingService: Optional[EmbeddingService] = get_embedding_service()
        except Exception as e:
            self.embeddingService = None
            logger.warning(f"EmbeddingService 初始化失败，向量检索不可用: {e}")
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
                prompt: str = self.get_prompt(message, db)
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

                prompt: str = self.get_prompt(message, db)
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
                        # 检测内容长度是否超过固定阈值（超过200字符视为异常增长）
                        if current_length > 20:
                            logger.info(f"检测到内容长度过长: {current_length} 字符，跳过此内容")
                            continue
                        previous_length = current_length
                        yield content
            except Exception as e:
                logger.error(f"流式聊天异常: {str(e)}")
                if "4015" in str(e):
                    yield "机器人未发布到 API 频道"
                else:
                    yield f"流式聊天服务异常: {str(e)}"

    # TODO: 抽离所有构建prompt的方法
    def search_article_from_db(self, message: str = "", db: Session = Depends(get_db)) -> str:
            articles: List[Article] = self.articleMapper.get_all_articles_mapper(db)
            if not articles:
                return "没有找到相关的知识库内容"

            message_text: str = (message or "").strip()
            article_map: Dict[int, Article] = {article.id: article for article in articles if article.id is not None}
            sorted_articles: List[Article] = sorted(
                articles,
                key=lambda item: item.create_at if item.create_at else datetime.min,
                reverse=True
            )[:100]

            total_articles: int = len(articles)
            selected_articles: List[Article] = []

            if total_articles < 5:
                logger.info("文章总数少于5，使用所有文章")
                selected_articles = sorted_articles
            else:
                logger.info("文章总数大于等于5，进行RAG检索")
                rag_candidates: List[Article] = []
                if message_text and getattr(self, "embeddingService", None):
                    query_vector: Optional[List[float]] = self.embeddingService.encode_text(message_text)
                    if query_vector and any(value != 0.0 for value in query_vector):
                        pg_generator = None
                        try:
                            pg_generator = get_pg_db()
                            pg_db = next(pg_generator)
                            if getattr(self, "vectorMapper", None) and pg_db is not None:
                                rag_results: List[Dict[str, Any]] = self.vectorMapper.search_similar_articles(pg_db, query_vector, limit=5)
                                seen_ids: set[int] = set()
                                for item in rag_results:
                                    article_id = item.get("article_id")
                                    if article_id in article_map and article_id not in seen_ids:
                                        rag_candidates.append(article_map[article_id])
                                        seen_ids.add(article_id)
                            else:
                                logger.warning("向量检索依赖未就绪，降级为默认文章列表")
                        except StopIteration:
                            logger.warning("PostgreSQL 连接不可用，降级为默认文章列表")
                        except Exception as rag_error:
                            logger.warning(f"向量检索失败，降级为默认文章列表: {rag_error}")
                        finally:
                            if pg_generator is not None:
                                try:
                                    pg_generator.close()
                                except Exception:
                                    pass
                    else:
                        logger.info("缺少有效的向量编码结果，降级使用默认文章列表")

                if rag_candidates:
                    selected_articles = rag_candidates[:5]
                else:
                    selected_articles = sorted_articles[:5]

                if len(selected_articles) < 5:
                    for article in sorted_articles:
                        if article not in selected_articles:
                            selected_articles.append(article)
                        if len(selected_articles) >= 5:
                            break

            content_list: List[str] = []
            # TODO：所有方式得到的文章都拼接完整内容
            # 如果这些文章是通过 RAG 检索得到的(即在 rag_candidates 中)，则拼接完整内容；否则保留摘要
            rag_ids = {a.id for a in rag_candidates} if 'rag_candidates' in locals() and rag_candidates else set()
            for article in selected_articles:
                if article.id in rag_ids:
                    article_content = article.content or ""
                else:
                    # 非 RAG 命中时使用摘要，防止 prompt 过大
                    article_content = (article.content or "")[:200]

                content_list.append(
                    f"标题: {article.title}, 内容(Markdown格式，自行转换): {article_content}, 用户ID: {article.user_id}, 标签: {article.tags}, 状态: {article.status}, 创建时间: {article.create_at.isoformat() if article.create_at else '未知'}, 更新时间: {article.update_at.isoformat() if article.update_at else '未知'}, 浏览量: {article.views}"
                )
            return "\n".join(content_list) if content_list else "没有找到相关的知识库内容"
        
    def search_user_from_db(self,db: Session = Depends(get_db)) -> str:
            users: List[User] = self.userMapper.get_all_users_mapper(db)
            if not users:
                return "没有找到相关的用户信息"
            user_list: List[str] = []
            for user in users:
                user_list.append(f"ID: {user.id}, 名称: {user.name}, 年龄: {user.age}, 邮箱: {user.email}, 角色: {user.role}")
            return "\n".join(user_list) if user_list else "没有找到相关的用户信息"
        
    def search_category_from_db(self,db: Session = Depends(get_db)) -> str:
            categories: List[Dict[str, Any]] = self.categoryMapper.get_all_categories_mapper(db)
            if not categories:
                return "没有找到相关的分类信息"
            category_list: List[str] = []
            for category in categories:
                category_list.append(f"分类ID: {category.id}, 名称: {category.name}")
            return "\n".join(category_list) if category_list else "没有找到相关的分类信息"
        
    def search_sub_category_from_db(self,db: Session = Depends(get_db)) -> str:
            sub_categories: List[SubCategory] = self.subCategoryMapper.get_all_subcategories_mapper(db)
            if not sub_categories:
                return "没有找到相关的子分类信息"
            sub_category_list: List[str] = []
            for sub_category in sub_categories:
                sub_category_list.append(f"子分类ID: {sub_category.id}, 名称: {sub_category.name}, 所属分类ID: {sub_category.category_id}")
            return "\n".join(sub_category_list) if sub_category_list else "没有找到相关的子分类信息"
        
    def search_logs_from_db(self) -> str:
            cursor: Any = self.articleLogMapper.get_all_articlelogs_limit_mapper()
            log_list: List[str] = []
            for log in cursor:
                log_str: str = ", ".join([f"{k}: {v}" for k, v in log.items()])
                log_list.append(log_str)
            return "\n".join(log_list) if log_list else "没有找到相关的日志信息"
        
    def search_ai_history_from_db(self, db: Session = Depends(get_db), user_id: int = 0) -> str:
            histories = self.aiHistoryMapper.get_all_ai_history_by_userid(db, user_id=user_id, limit=3) # 限制返回最近3条记录
            if not histories:
                return "没有找到相关的AI历史记录"
            history_list: List[str] = []
            for history in histories:
                history_list.append(f"用户ID: {history.user_id}, 提问: {history.ask}, 回复: {history.reply}, AI类型: {history.ai_type}")
            return "\n".join(history_list) if history_list else "没有找到相关的AI历史记录"
        
    def get_prompt(self,message: str, db: Session = Depends(get_db)) -> str:
            user_id: str = get_current_user_id() or ""
            username: str = get_current_username() or ""
            userInfo: str = f"用户ID: {user_id}, 用户名: {username}"
            article: str = self.search_article_from_db(message, db)
            user: str = self.search_user_from_db(db)
            category: str = self.search_category_from_db(db)
            sub_category: str = self.search_sub_category_from_db(db)
            logs: str = self.search_logs_from_db()
            ai_history = self.search_ai_history_from_db(db, user_id=int(user_id) if user_id.isdigit() else 0)
            knowledge: str = (f"当前用户信息(提问的用户，一般会称“我”)：{userInfo}\n文章信息：{article}\n用户信息：{user}\n分类信息：{category}\n日志信息：{logs}"
            f"\n子分类信息：{sub_category}\n用户的历史记录：{ai_history}")
            prompt: str = f"已知信息如下：{knowledge}\n用户提问：{message}"
            return prompt

@lru_cache()
def get_coze_service(articleMapper: ArticleMapper = Depends(get_article_mapper), userMapper: UserMapper = Depends(get_user_mapper), categoryMapper: CategoryMapper = Depends(get_category_mapper), subCategoryMapper: SubCategoryMapper = Depends(get_subcategory_mapper), articleLogMapper: ArticleLogMapper = Depends(get_articlelog_mapper), aiHistoryMapper: AiHistoryMapper = Depends(get_ai_history_mapper)) -> CozeService:
    return CozeService(articleMapper, userMapper, articleLogMapper, subCategoryMapper, categoryMapper, aiHistoryMapper)