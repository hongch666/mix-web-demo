import asyncio
import os
import re
from functools import lru_cache
from typing import Any, Optional

import sqlalchemy
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session

from app.core.base import Logger
from app.core.config import load_config
from app.core.constants import HttpCode, Messages, VectorConstants
from app.core.db import get_pgvector_connection_string
from app.core.errors import BusinessException

DocScore = tuple[Document, float]


class VectorMapper:
    """PostgreSQL 向量库 Mapper

    封装 PGVector 的写入、删除、检索与元数据查询；文章文档的构建（注入清洗、文本切分、
    元数据拼装）属于「以什么粒度落库」，一并收在这里，上层只需给出文章原文

    PGVector 的入库与检索都依赖 embedding 模型，因此该模型也由本 Mapper 持有
    """

    def __init__(
        self,
        embedding_function: Any,
        collection_name: str = VectorConstants.COLLECTION_NAME,
    ) -> None:
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=VectorConstants.CHUNK_SIZE,
            chunk_overlap=VectorConstants.CHUNK_OVERLAP,
            length_function=len,
            separators=VectorConstants.CHUNK_SEPARATORS,
        )
        Logger.info(Messages.TEXT_SPLITTER_INITIALIZATION_SUCCESS)
        self._vector_store = PGVector(
            embedding_function=embedding_function,
            collection_name=collection_name,
            connection_string=get_pgvector_connection_string(),
            use_jsonb=True,
        )
        Logger.info(Messages.VECTOR_STORE_INITIALIZATION_SUCCESS)

    @staticmethod
    def sanitize_content(text: str) -> str:
        """清洗向量内容的 Prompt 注入文本

        向量库承载的是直接喂给 LLM 的文本，入库前与检索侧共用同一份规则，
        避免注入指令随文章内容长期留在库里

        Args:
            text: 原始文本

        Returns:
            清洗后的文本，恶意片段替换为占位符
        """
        for pattern in VectorConstants.INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                Logger.warning(Messages.RAG_TOOL_PROMPT_INJECTION_DETECTED())
                text = re.sub(
                    pattern,
                    Messages.RAG_TOOL_FILTERED_PLACEHOLDER(),
                    text,
                    flags=re.IGNORECASE,
                )
        return text

    @staticmethod
    def _resolve_embedding_api_key(embedding_cfg: dict[str, Any]) -> str:
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

    async def upsert_articles(
        self,
        article_ids: list[int],
        titles: list[str],
        contents: list[str],
        metadata_list: Optional[list[dict[str, Any]]] = None,
    ) -> int:
        """写入文章向量，返回写入的向量条数

        调用方负责先按文章 ID 清理同 ID 的旧向量，本方法只做追加，
        失败会向上抛出，由调用方决定重试或放弃

        Args:
            article_ids: 文章ID列表
            titles: 文章标题列表
            contents: 文章内容列表
            metadata_list: 附加元数据列表（可选，与文章下标一一对应）

        Returns:
            实际写入的向量条数
        """
        documents: list[Document] = self._build_article_documents(
            article_ids, titles, contents, metadata_list
        )
        if not documents:
            return 0

        await asyncio.to_thread(self._vector_store.add_documents, documents)
        Logger.info(Messages.RAG_BATCH_ADDED_ARTICLES(len(article_ids), len(documents)))
        return len(documents)

    async def delete_by_article_ids(self, article_ids: list[int]) -> int:
        """按文章 ID 删除向量，返回删除的向量条数"""
        if not article_ids:
            return 0
        return await asyncio.to_thread(self._delete_by_article_ids_sync, article_ids)

    async def list_article_ids(self) -> set[int]:
        """列出向量库中已存在的文章 ID"""
        return await asyncio.to_thread(self._list_article_ids_sync)

    async def similarity_search_with_score(
        self,
        query: str,
        k: int,
        metadata_filter: Optional[dict[str, Any]] = None,
    ) -> list[DocScore]:
        """按相似度检索向量，返回 (Document, score) 列表"""
        return await asyncio.to_thread(
            self._vector_store.similarity_search_with_score,
            query,
            k,
            metadata_filter,
        )

    def as_retriever(self, k: int) -> Any:
        """获取 LangChain 检索器（纯对象构造，无 IO）"""
        return self._vector_store.as_retriever(search_kwargs={"k": k})

    def _build_article_documents(
        self,
        article_ids: list[int],
        titles: list[str],
        contents: list[str],
        metadata_list: Optional[list[dict[str, Any]]],
    ) -> list[Document]:
        """把文章原文拆成待入库的文档块"""
        documents: list[Document] = []
        for i, (article_id, title, content) in enumerate(
            zip(article_ids, titles, contents)
        ):
            # 合并标题和内容，入库前过滤恶意注入文本
            full_text = self.sanitize_content(f"# {title}\n\n{content}")
            chunks: list[str] = self._text_splitter.split_text(full_text)

            for j, chunk in enumerate(chunks):
                metadata: dict[str, Any] = {
                    "article_id": article_id,
                    "title": title,
                    "chunk_index": j,
                    "total_chunks": len(chunks),
                }
                if metadata_list and i < len(metadata_list):
                    metadata.update(metadata_list[i])
                documents.append(Document(page_content=chunk, metadata=metadata))
        return documents

    def _delete_by_article_ids_sync(self, article_ids: list[int]) -> int:
        """同步删除向量记录，由 delete_by_article_ids 调度到线程池执行"""
        with Session(self._vector_store._bind) as session:
            collection: Any = self._get_collection(session)
            if collection is None:
                return 0
            statement: Any = sqlalchemy.delete(self._vector_store.EmbeddingStore).where(
                self._vector_store.EmbeddingStore.collection_id == collection.uuid,
                self._vector_store.EmbeddingStore.cmetadata["article_id"]
                .astext.in_([str(article_id) for article_id in article_ids]),
            )
            deleted: int = int(session.execute(statement).rowcount or 0)
            session.commit()

        Logger.info(Messages.RAG_DELETE_ARTICLES_SUCCESS(deleted, len(article_ids)))
        return deleted

    def _list_article_ids_sync(self) -> set[int]:
        """同步查询向量库内的文章 ID，由 list_article_ids 调度到线程池执行"""
        with Session(self._vector_store._bind) as session:
            collection: Any = self._get_collection(session)
            if collection is None:
                return set()
            statement: Any = sqlalchemy.select(
                sqlalchemy.distinct(
                    self._vector_store.EmbeddingStore.cmetadata["article_id"].astext
                )
            ).where(self._vector_store.EmbeddingStore.collection_id == collection.uuid)
            rows: list[Any] = list(session.execute(statement).scalars().all())

        article_ids: set[int] = set()
        for row in rows:
            try:
                article_ids.add(int(row))
            except (TypeError, ValueError):
                continue
        return article_ids

    def _get_collection(self, session: Session) -> Any:
        """获取当前向量存储对应的 collection 记录"""
        return self._vector_store.CollectionStore.get_by_name(
            session, self._vector_store.collection_name
        )


@lru_cache
def get_vector_embeddings() -> Any:
    """获取向量库使用的 embedding 模型"""
    embedding_cfg = (load_config("agent") or {}).get("embedding", {})
    api_key: str = VectorMapper._resolve_embedding_api_key(embedding_cfg)
    embedding_model = str(embedding_cfg.get("embedding_model"))

    if not api_key:
        raise BusinessException(
            Messages.EMBEDDING_CONFIG_INCOMPLETE_MESSAGE,
            HttpCode.SERVICE_UNAVAILABLE,
            Messages.ERROR_INITIALIZATION_ERROR,
        )

    try:
        embeddings = DashScopeEmbeddings(
            model=embedding_model, dashscope_api_key=api_key
        )
        Logger.info(Messages.EMBEDDING_MODEL_INITIALIZED(embedding_model))
        return embeddings
    except Exception as error:
        raise BusinessException(
            Messages.EMBEDDING_INIT_FAILED(error),
            HttpCode.SERVICE_UNAVAILABLE,
            Messages.ERROR_INITIALIZATION_ERROR,
        )


@lru_cache()
def get_vector_store_mapper(embedding_function: Any) -> VectorMapper:
    return VectorMapper(embedding_function)
