from functools import lru_cache
from typing import List, Dict, Any, Optional
from fastapi import Depends
from sqlmodel import Session
from api.mapper import ArticleMapper,get_article_mapper,UserMapper,get_user_mapper,ArticleLogMapper,get_articlelog_mapper,SubCategoryMapper,get_subcategory_mapper,CategoryMapper,get_category_mapper,AiHistoryMapper,get_ai_history_mapper,VectorMapper, get_vector_mapper
from api.service import EmbeddingService, get_embedding_service
from common.utils import fileLogger as logger
from config import get_db, get_pg_db, load_config
from entity.po import Article,User,SubCategory
from common.middleware import get_current_user_id, get_current_username
from datetime import datetime

class PromptService:
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
        self.topK = load_config("embedding").get("top_k", 5) if load_config("embedding") else 5

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

            if total_articles < self.topK:
                logger.info(f"文章总数少于{self.topK}，使用所有文章")
                selected_articles = sorted_articles
            else:
                logger.info(f"文章总数大于等于{self.topK}，进行RAG检索")
                rag_candidates: List[Article] = []
                if message_text and getattr(self, "embeddingService", None):
                    query_vector: Optional[List[float]] = self.embeddingService.encode_text(message_text)
                    if query_vector and any(value != 0.0 for value in query_vector):
                        pg_generator = None
                        try:
                            pg_generator = get_pg_db()
                            pg_db = next(pg_generator)
                            if getattr(self, "vectorMapper", None) and pg_db is not None:
                                rag_results: List[Dict[str, Any]] = self.vectorMapper.search_similar_articles(pg_db, query_vector, limit=self.topK)
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
                    selected_articles = rag_candidates[:self.topK]
                else:
                    selected_articles = sorted_articles[:self.topK]

                if len(selected_articles) < self.topK:
                    for article in sorted_articles:
                        if article not in selected_articles:
                            selected_articles.append(article)
                        if len(selected_articles) >= self.topK:
                            break

            content_list: List[str] = []
            # 所有方式得到的文章都拼接完整内容
            for article in selected_articles:
                # 使用完整内容
                article_content = article.content or ""

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
def get_prompt_service(articleMapper: ArticleMapper = Depends(get_article_mapper), userMapper: UserMapper = Depends(get_user_mapper), categoryMapper: CategoryMapper = Depends(get_category_mapper), subCategoryMapper: SubCategoryMapper = Depends(get_subcategory_mapper), articleLogMapper: ArticleLogMapper = Depends(get_articlelog_mapper), aiHistoryMapper: AiHistoryMapper = Depends(get_ai_history_mapper)) -> PromptService:
    return PromptService(articleMapper, userMapper, articleLogMapper, subCategoryMapper, categoryMapper, aiHistoryMapper)