import os
import re
import warnings
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from app.core.base import Logger
from app.core.config import load_config
from app.core.constants import HttpCode, Messages, Prompts
from app.core.db import get_pgvector_connection_string
from app.core.errors import BusinessException
from app.internal.agents.langsmith import get_langsmith_context
from langchain_community.cache import InMemoryCache
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.documents import Document
from langchain_core.globals import set_llm_cache
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 抑制 PGVector 弃用警告
warnings.filterwarnings("ignore", category=DeprecationWarning)

DocScore = Tuple[Document, float]

# Prompt 注入防御模式（用于过滤 RAG 检索内容中的恶意文本）
_INJECTION_PATTERNS: List[str] = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"you\s+are\s+(now\s+)?DAN",
    r"from\s+now\s+on\s+you\s+are",
    r"\[SYSTEM\]",
    r"output\s+(your|all)\s+(system\s+)?prompt",
    r"reveal\s+(your|the)\s+(instructions?|api.?key)",
    r"pretend\s+(you\s+are|to\s+be)",
    r"act\s+as\s+if\s+you\s+are",
]


def sanitize_retrieved_content(text: str) -> str:
    """过滤 RAG 检索内容中的 Prompt 注入文本

    Args:
        text: 原始检索内容

    Returns:
        过滤后的内容，恶意片段替换为 [已过滤]
    """
    for pattern in _INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            Logger.warning(Messages.RAG_TOOL_PROMPT_INJECTION_DETECTED())
            text = re.sub(pattern, Messages.RAG_TOOL_FILTERED_PLACEHOLDER(), text, flags=re.IGNORECASE)
    return text


class RAGTools:
    """RAG工具类 - 基于LangChain实现

    支持 HyDE 检索增强、Prompt 注入防御、元数据过滤、Embedding 缓存。
    """

    def __init__(self) -> None:
        """初始化RAG组件"""

        self.logger = Logger
        self.enabled: bool = True
        self._init_error_message: Optional[str] = None

        # 0. 启用 Embedding 缓存（避免重复计算相同文本的向量）
        try:
            set_llm_cache(InMemoryCache())
            self.logger.info(Messages.EMBEDDING_CACHE_ENABLED())
        except Exception as cache_error:
            self.logger.warning(Messages.EMBEDDING_CACHE_ENABLE_FAILED(cache_error))

        # 1. 初始化嵌入模型
        embedding_cfg = (load_config("agent") or {}).get("embedding", {})

        api_key = self._resolve_embedding_api_key(embedding_cfg)
        embedding_model = str(embedding_cfg.get("embedding_model"))
        self.top_k = int(embedding_cfg.get("top_k"))
        self.similarity_threshold = float(embedding_cfg.get("similarity_threshold"))
        self.similarity_tolerance = float(embedding_cfg.get("similarity_tolerance"))

        if not api_key:
            self.enabled = False
            self._init_error_message = Messages.EMBEDDING_CONFIG_INCOMPLETE_MESSAGE
            raise BusinessException(
                self._init_error_message,
                HttpCode.SERVICE_UNAVAILABLE,
                Messages.ERROR_INITIALIZATION_ERROR,
            )

        try:
            self.embeddings = DashScopeEmbeddings(
                model=embedding_model, dashscope_api_key=api_key
            )
            self.logger.info(Messages.EMBEDDING_MODEL_INITIALIZED(embedding_model))
        except Exception as error:
            self.enabled = False
            self._init_error_message = (
                Messages.EMBEDDING_INIT_FAILED(error)
            )
            raise BusinessException(
                self._init_error_message,
                HttpCode.SERVICE_UNAVAILABLE,
                Messages.ERROR_INITIALIZATION_ERROR,
            )

        # 1.5 初始化 HyDE LLM（复用已配置的模型，用于生成假设性文档增强检索精度）
        self.hyde_llm: Optional[Any] = None
        agent_cfg: Dict[str, Any] = (load_config("agent") or {}).get("closeai", {})
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
                self.logger.warning(
                    Messages.HYDE_LLM_INIT_FAILED(hyde_error)
                )

        # 2. 初始化文本切分器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
        )
        self.logger.info(Messages.TEXT_SPLITTER_INITIALIZATION_SUCCESS)

        # 3. 初始化PostgreSQL向量存储
        connection_string = get_pgvector_connection_string()

        self.vector_store = PGVector(
            embedding_function=self.embeddings,
            collection_name="articles",
            connection_string=connection_string,
            use_jsonb=True,
        )
        self.logger.info(Messages.VECTOR_STORE_INITIALIZATION_SUCCESS)

    @staticmethod
    def _resolve_embedding_api_key(embedding_cfg: Dict[str, Any]) -> str:
        """优先从配置读取 embedding key，再回退到常见环境变量"""
        candidates = [
            embedding_cfg.get("api_key"),
            os.getenv("EMBEDDING_API_KEY"),
            os.getenv("DASHSCOPE_API_KEY"),
            os.getenv("DASHSCOPE_API_KEY_FOR_LLM"),
        ]
        for candidate in candidates:
            if candidate and str(candidate).strip():
                return str(candidate).strip()
        return ""

    def _build_disabled_message(self) -> str:
        return self._init_error_message or Messages.RAG_SERVICE_NOT_INITIALIZED_MESSAGE

    async def add_articles_to_vector_store(
        self,
        article_ids: List[int],
        titles: List[str],
        contents: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        将文章添加到向量存储

        Args:
            article_ids: 文章ID列表
            titles: 文章标题列表
            contents: 文章内容列表
            metadata_list: 元数据列表（可选）

        Returns:
            操作结果描述
        """
        try:
            documents: List[Document] = []

            for i, (article_id, title, content) in enumerate(
                zip(article_ids, titles, contents)
            ):
                # 合并标题和内容，入库前过滤恶意注入文本
                full_text = f"# {title}\n\n{content}"
                full_text = sanitize_retrieved_content(full_text)

                # 切分文本
                chunks = self.text_splitter.split_text(full_text)

                # 为每个块创建Document对象
                for j, chunk in enumerate(chunks):
                    metadata = {
                        "article_id": article_id,
                        "title": title,
                        "chunk_index": j,
                        "total_chunks": len(chunks),
                    }

                    # 添加额外的元数据
                    if metadata_list and i < len(metadata_list):
                        metadata.update(metadata_list[i])

                    documents.append(Document(page_content=chunk, metadata=metadata))

            # 批量添加到向量存储
            self.vector_store.add_documents(documents)

            result = Messages.RAG_BATCH_ADDED_ARTICLES(len(article_ids), len(documents))
            self.logger.info(result)
            return result

        except Exception as e:
            error_msg = Messages.RAG_BATCH_ADD_FAILED(e)
            self.logger.error(error_msg)
            return error_msg

    def _deduplicate_articles(
        self, docs_with_scores: List[DocScore], k: int
    ) -> List[DocScore]:
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

        result: List[DocScore] = []
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
        tags_filter: Optional[List[str]] = None,
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
                        hyde_prompt = (
                            Prompts.HYDE_GENERATION_PROMPT(query)
                        )
                        hypothetical_doc = await self.hyde_llm.ainvoke(hyde_prompt)
                        search_query = (
                            hypothetical_doc.content
                            if hasattr(hypothetical_doc, "content")
                            else str(hypothetical_doc)
                        )
                        self.logger.info(
                            Messages.HYDE_GENERATION_SUCCESS(len(query), len(search_query))
                        )
                    except Exception as hyde_error:
                        self.logger.warning(
                            Messages.HYDE_GENERATION_FAILED(hyde_error)
                        )
                        search_query = query

            # 构建元数据过滤器（pgvector JSONB 过滤）
            pgvector_filter: Optional[Dict[str, Any]] = None
            if tags_filter or user_id_filter is not None:
                conditions: List[Dict[str, Any]] = []
                if tags_filter:
                    conditions.append({"tags": {"$in": tags_filter}})
                if user_id_filter is not None:
                    conditions.append({"user_id": user_id_filter})
                pgvector_filter = (
                    {"$and": conditions} if len(conditions) > 1 else conditions[0]
                )

            # 使用向量存储进行相似度搜索（含元数据过滤）
            docs = self.vector_store.similarity_search_with_score(
                search_query, k=fetch_k, filter=pgvector_filter
            )

            # 根据相似度阈值过滤结果
            filtered_docs: List[DocScore] = [
                (doc, score)
                for doc, score in docs
                if score >= self.similarity_threshold
            ]

            if not filtered_docs:
                return Messages.NO_RELEVANT_ARTICLES_FOUND_MESSAGE

            # 对相似文章进行智能去重处理
            dedup_docs = self._deduplicate_articles(filtered_docs, search_k)

            self.logger.info(
                Messages.RAG_SEARCH_SUCCESS(len(dedup_docs), len(filtered_docs), len(docs))
            )

            # 格式化结果（检索后过滤恶意注入文本）
            result_text = Messages.RAG_SEARCH_RESULT_HEADER(len(dedup_docs), self.similarity_threshold)

            for i, (doc, score) in enumerate(dedup_docs, 1):
                article_id = doc.metadata.get("article_id", "未知")
                title = doc.metadata.get("title", "无标题")
                chunk_index = doc.metadata.get("chunk_index", 0)
                content = doc.page_content

                # 检索后过滤恶意注入文本
                content = sanitize_retrieved_content(content)

                result_text += Messages.RAG_RESULT_ARTICLE_LINE(i, article_id, title)
                result_text += Messages.RAG_RESULT_SIMILARITY_SCORE(score)
                result_text += (
                    Messages.RAG_RESULT_CONTENT_FRAGMENT(chunk_index + 1, len(content))
                )
                result_text += f"   {content}\n\n"

            self.logger.info(
                Messages.RAG_SEARCH_SUCCESS(len(dedup_docs), len(filtered_docs), len(docs))
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

    async def get_article_context(self, query: str, k: int = 3) -> List[Document]:
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

            docs_with_scores = self.vector_store.similarity_search_with_score(
                query, k=fetch_k
            )

            # 对相似文章进行智能去重处理
            dedup_docs_with_scores = self._deduplicate_articles(docs_with_scores, k)

            # 提取Document对象
            dedup_docs = [doc for doc, _ in dedup_docs_with_scores]

            self.logger.info(
                Messages.RAG_CONTEXT_FETCH_SUCCESS(len(dedup_docs), len(docs_with_scores))
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

    def get_langchain_tools(self) -> List[Tool]:
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
        return self.vector_store.as_retriever(search_kwargs={"k": search_k})


@lru_cache
def get_rag_tools() -> RAGTools:
    """获取RAG工具实例"""
    return RAGTools()
