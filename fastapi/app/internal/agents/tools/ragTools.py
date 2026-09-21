import warnings
from functools import lru_cache
from typing import Any, Optional

from langchain_community.cache import InMemoryCache
from langchain_core.documents import Document
from langchain_core.globals import set_llm_cache
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI

from app.core.base import Logger
from app.core.config import load_config
from app.core.constants import Messages, Prompts
from app.internal.agents.langsmith import get_langsmith_context
from app.internal.crud import DocScore, VectorMapper

# 抑制 PGVector 弃用警告
warnings.filterwarnings("ignore", category=DeprecationWarning)


class RAGTools:
    """RAG工具类 - 基于LangChain实现

    向量库的读写统一走 VectorMapper，本类只保留检索侧语义：
    HyDE 检索增强、Prompt 注入防御、元数据过滤、结果去重
    """

    def __init__(self, vector_mapper: VectorMapper) -> None:
        """初始化RAG组件"""

        self.logger = Logger
        self.enabled: bool = True
        self._init_error_message: Optional[str] = None
        self._vector_mapper = vector_mapper

        # 启用 Embedding 缓存（避免重复计算相同文本的向量）
        try:
            set_llm_cache(InMemoryCache())
            self.logger.info(Messages.EMBEDDING_CACHE_ENABLED())
        except Exception as cache_error:
            self.logger.warning(Messages.EMBEDDING_CACHE_ENABLE_FAILED(cache_error))

        # 检索参数
        embedding_cfg = (load_config("agent") or {}).get("embedding", {})
        self.top_k = int(embedding_cfg.get("top_k"))
        self.similarity_threshold = float(embedding_cfg.get("similarity_threshold"))
        self.similarity_tolerance = float(embedding_cfg.get("similarity_tolerance"))

        # HyDE LLM（复用已配置的模型，用于生成假设性文档增强检索精度）
        self.hyde_llm: Optional[Any] = None
        agent_cfg: dict[str, Any] = (load_config("agent") or {}).get("closeai", {})
        if agent_cfg.get("api_key") and agent_cfg.get("base_url"):
            try:
                self.hyde_llm = ChatOpenAI(
                    model=agent_cfg.get("model_name", "gpt-3.5-turbo"),
                    api_key=agent_cfg["api_key"],
                    base_url=agent_cfg["base_url"],
                    temperature=0.3,
                    max_tokens=300,
                    timeout=10,
                )
                self.logger.info(Messages.HYDE_LLM_INITIALIZED())
            except Exception as hyde_error:
                self.logger.warning(Messages.HYDE_LLM_INIT_FAILED(hyde_error))

    def _build_disabled_message(self) -> str:
        return self._init_error_message or Messages.RAG_SERVICE_NOT_INITIALIZED_MESSAGE

    def _deduplicate_articles(
        self, docs_with_scores: list[DocScore], k: int
    ) -> list[DocScore]:
        """
        对相似文章进行去重处理，保留相近相似度下的不同文章片段

        Args:
            docs_with_scores: (Document, score) 的元组列表，已按相似度排序
            k: 目标返回数量

        Returns:
            去重后的 (Document, score) 列表
        """
        if not docs_with_scores:
            return []

        result: list[DocScore] = []
        seen_articles: set[Any] = set()
        last_score: Optional[float] = None

        for doc, score in docs_with_scores:
            article_id = doc.metadata.get("article_id")

            # 首个结果或得分差异超过容差的结果，直接添加
            if last_score is None or (last_score - score) > self.similarity_tolerance:
                result.append((doc, score))
                seen_articles.add(article_id)
                last_score = score
                if len(result) >= k:
                    break
            else:
                # 在相近相似度的范围内，优先选择不同的文章
                if article_id not in seen_articles:
                    result.append((doc, score))
                    seen_articles.add(article_id)
                    if len(result) >= k:
                        break

        # 如果结果不足k个，继续添加相同文章的其他片段
        if len(result) < k:
            for doc, score in docs_with_scores:
                if (doc, score) not in result and len(result) < k:
                    result.append((doc, score))

        return result

    async def search_similar_articles(
        self,
        query: str,
        k: int = 5,
        use_hyde: bool = True,
        tags_filter: Optional[list[str]] = None,
        user_id_filter: Optional[int] = None,
    ) -> str:
        """
        搜索相似文章

        Args:
            query: 查询文本
            k: 返回结果数量（默认使用配置中的top_k，如果传入则使用传入值）
            use_hyde: 是否启用 HyDE 假设性文档检索增强
            tags_filter: 按标签过滤（可选）
            user_id_filter: 按作者ID过滤（可选）

        Returns:
            相似文章的文本描述
        """
        try:
            if not self.enabled:
                return self._build_disabled_message()

            # 如果未明确传入k值，使用配置中的top_k
            search_k = k if k != 5 else self.top_k
            fetch_k = max(search_k * 6, 30)

            # HyDE: 用 LLM 生成假设性回答替代原始短查询，提升检索精度
            search_query: str = query
            if use_hyde and self.hyde_llm is not None:
                with get_langsmith_context(
                    name="rag.hyde",
                    tags=["feature:rag", "stage:hyde"],
                    metadata={
                        "query_length": len(query),
                        "hyde_enabled": True,
                    },
                ):
                    try:
                        hyde_prompt = Prompts.HYDE_GENERATION_PROMPT(query)
                        hypothetical_doc = await self.hyde_llm.ainvoke(hyde_prompt)
                        search_query = (
                            hypothetical_doc.content
                            if hasattr(hypothetical_doc, "content")
                            else str(hypothetical_doc)
                        )
                        self.logger.info(
                            Messages.HYDE_GENERATION_SUCCESS(
                                len(query), len(search_query)
                            )
                        )
                    except Exception as hyde_error:
                        self.logger.warning(Messages.HYDE_GENERATION_FAILED(hyde_error))
                        search_query = query

            # 构建元数据过滤器（pgvector JSONB 过滤）
            pgvector_filter: Optional[dict[str, Any]] = None
            if tags_filter or user_id_filter is not None:
                conditions: list[dict[str, Any]] = []
                if tags_filter:
                    conditions.append({"tags": {"$in": tags_filter}})
                if user_id_filter is not None:
                    conditions.append({"user_id": user_id_filter})
                pgvector_filter = (
                    {"$and": conditions} if len(conditions) > 1 else conditions[0]
                )

            # 使用向量存储进行相似度搜索（含元数据过滤）
            docs = await self._vector_mapper.similarity_search_with_score(
                search_query, fetch_k, pgvector_filter
            )

            # 根据相似度阈值过滤结果
            filtered_docs: list[DocScore] = [
                (doc, score)
                for doc, score in docs
                if score >= self.similarity_threshold
            ]

            if not filtered_docs:
                return Messages.NO_RELEVANT_ARTICLES_FOUND_MESSAGE

            # 对相似文章进行智能去重处理
            dedup_docs = self._deduplicate_articles(filtered_docs, search_k)

            self.logger.info(
                Messages.RAG_SEARCH_SUCCESS(
                    len(dedup_docs), len(filtered_docs), len(docs)
                )
            )

            # 格式化结果（检索后过滤恶意注入文本）
            result_text = Messages.RAG_SEARCH_RESULT_HEADER(
                len(dedup_docs), self.similarity_threshold
            )

            for i, (doc, score) in enumerate(dedup_docs, 1):
                article_id = doc.metadata.get("article_id", "未知")
                title = doc.metadata.get("title", "无标题")
                chunk_index = doc.metadata.get("chunk_index", 0)
                content = doc.page_content

                # 检索后过滤恶意注入文本
                content = VectorMapper.sanitize_content(content)

                result_text += Messages.RAG_RESULT_ARTICLE_LINE(i, article_id, title)
                result_text += Messages.RAG_RESULT_SIMILARITY_SCORE(score)
                result_text += Messages.RAG_RESULT_CONTENT_FRAGMENT(
                    chunk_index + 1, len(content)
                )
                result_text += f"   {content}\n\n"

            self.logger.info(
                Messages.RAG_SEARCH_SUCCESS(
                    len(dedup_docs), len(filtered_docs), len(docs)
                )
            )
            return result_text

        except Exception as e:
            error_text = str(e)
            if (
                "InvalidApiKey" in error_text
                or "Invalid API-key provided" in error_text
            ):
                self.enabled = False
                self._init_error_message = Messages.EMBEDDING_CONFIG_INCOMPLETE_MESSAGE
                self.logger.error(self._init_error_message)
                return self._init_error_message
            error_msg = Messages.RAG_SEARCH_FAILED(e)
            self.logger.error(error_msg)
            return error_msg

    async def get_article_context(self, query: str, k: int = 3) -> list[Document]:
        """
        获取文章上下文（供Chain使用）

        Args:
            query: 查询文本
            k: 返回结果数量

        Returns:
            Document对象列表
        """
        try:
            if not self.enabled:
                return []

            # 搜索更多结果以便进行智能去重
            fetch_k = max(k * 3, 10)

            docs_with_scores = await self._vector_mapper.similarity_search_with_score(
                query, fetch_k
            )

            # 对相似文章进行智能去重处理
            dedup_docs_with_scores = self._deduplicate_articles(docs_with_scores, k)

            # 提取Document对象
            dedup_docs = [doc for doc, _ in dedup_docs_with_scores]

            self.logger.info(
                Messages.RAG_CONTEXT_FETCH_SUCCESS(
                    len(dedup_docs), len(docs_with_scores)
                )
            )
            return dedup_docs
        except Exception as e:
            error_text = str(e)
            if (
                "InvalidApiKey" in error_text
                or "Invalid API-key provided" in error_text
            ):
                self.enabled = False
                self._init_error_message = Messages.EMBEDDING_CONFIG_INCOMPLETE_MESSAGE
                self.logger.error(self._init_error_message)
                return []
            self.logger.error(Messages.RAG_CONTEXT_FETCH_FAILED(e))
            return []

    def get_langchain_tools(self) -> list[Tool]:
        """
        获取LangChain Tool对象列表

        Returns:
            Tool对象列表
        """

        async def _search_tool(query: str) -> str:
            return await self.search_similar_articles(query, k=self.top_k)

        return [
            Tool(
                name=Messages.RAG_TOOL_NAME,
                description=Prompts.RAG_TOOL_DESC,
                func=None,
                coroutine=_search_tool,
            )
        ]

    async def get_retriever(self, k: int = 3) -> Any:
        """
        获取LangChain检索器

        Args:
            k: 返回结果数量（默认使用配置中的top_k）

        Returns:
            VectorStoreRetriever对象
        """
        search_k = k if k != 3 else self.top_k
        return self._vector_mapper.as_retriever(search_k)


@lru_cache
def get_rag_tools(vector_mapper: VectorMapper) -> RAGTools:
    """获取RAG工具实例"""
    return RAGTools(vector_mapper)
