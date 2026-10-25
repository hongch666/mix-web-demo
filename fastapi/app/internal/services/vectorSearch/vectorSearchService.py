from __future__ import annotations

import time
from functools import lru_cache
from typing import Any, Optional

from app.core.base import Logger, LoggerProtocol
from app.core.constants import Defaults, Messages
from app.internal.agents import get_langsmith_context
from app.internal.crud import VectorMapper, get_vector_store_mapper
from app.internal.schemas import (
    VectorMatchedChunkDTO,
    VectorSearchEnhanceItemDTO,
    VectorSearchEnhanceReq,
    VectorSearchEnhanceResp,
)


class VectorSearchService:
    """向量搜索增强服务"""

    def __init__(
        self,
        enabled: bool = Defaults.VECTOR_SEARCH_ENABLED,
        candidate_limit: int = Defaults.VECTOR_SEARCH_CANDIDATE_LIMIT,
        fetch_multiplier: int = Defaults.VECTOR_SEARCH_FETCH_MULTIPLIER,
        max_matched_chunks: int = Defaults.VECTOR_SEARCH_MAX_MATCHED_CHUNKS,
        min_score: float = Defaults.VECTOR_SEARCH_MIN_SCORE,
        score_mode: str = Defaults.VECTOR_SEARCH_SCORE_MODE,
        vector_mapper: VectorMapper | None = None,
        logger: LoggerProtocol | None = None,
    ) -> None:
        """初始化向量搜索开关、候选上限、召回倍数、最低分阈值与打分模式，并注入向量 Mapper 与日志器"""
        self.enabled = enabled
        self.candidate_limit = max(candidate_limit, 1)
        self.fetch_multiplier = max(fetch_multiplier, 1)
        self.max_matched_chunks = max(max_matched_chunks, 1)
        self.min_score = min_score
        self.score_mode = (
            score_mode if score_mode in {"similarity", "distance"} else "similarity"
        )
        # 由依赖图注入；缺省时回退到工厂单例，保持手工构造可用
        self._vector_mapper: VectorMapper | None = vector_mapper
        # 日志器可注入，缺省回退全局单例
        self._logger: LoggerProtocol = logger or Logger

    async def enhance(self, req: VectorSearchEnhanceReq) -> VectorSearchEnhanceResp:
        """执行向量增强, 返回候选文章的语义分和命中片段"""
        if not self.enabled:
            return VectorSearchEnhanceResp()

        keyword = (req.keyword or "").strip()
        if not keyword or not req.articleIds:
            return VectorSearchEnhanceResp()

        article_ids = self._normalize_article_ids(req.articleIds, req.limit)
        if not article_ids:
            return VectorSearchEnhanceResp()

        query = self._build_query(keyword, req)
        fetch_k = self._resolve_fetch_k(req.topK, len(article_ids))

        search_start = time.time()
        vector_mapper = self._vector_mapper or get_vector_store_mapper()
        with get_langsmith_context(
            name="vector.enhance",
            tags=["feature:vector_search"],
            metadata={
                "candidate_count": len(article_ids),
                "query_length": len(query),
                "fetch_k": fetch_k,
                "min_score": self.min_score,
            },
        ):
            docs_with_scores = await vector_mapper.similarity_search_with_score(
                query,
                fetch_k,
            )
        search_elapsed = time.time() - search_start
        self._logger.info(
            Messages.VECTOR_ENHANCE_SEARCH_TIMING(search_elapsed, len(docs_with_scores))
        )

        article_id_set = set(article_ids)
        grouped_chunks: dict[int, list[VectorMatchedChunkDTO]] = {}
        best_scores: dict[int, float] = {}

        for doc, raw_score in docs_with_scores:
            article_id = self._to_int(doc.metadata.get("article_id"))
            if article_id is None or article_id not in article_id_set:
                continue

            score = self._normalize_score(raw_score)
            if score < self.min_score:
                continue

            chunk = VectorMatchedChunkDTO(
                articleId=article_id,
                title=str(doc.metadata.get("title") or ""),
                chunkIndex=self._to_int(doc.metadata.get("chunk_index")) or 0,
                score=round(score, 4),
                content=self._trim_content(doc.page_content),
            )

            grouped_chunks.setdefault(article_id, []).append(chunk)
            if article_id not in best_scores or score > best_scores[article_id]:
                best_scores[article_id] = score

        items = []
        for article_id in article_ids:
            if article_id not in best_scores:
                continue

            chunks = sorted(
                grouped_chunks.get(article_id, []),
                key=lambda item: item.score,
                reverse=True,
            )[: self.max_matched_chunks]
            score = round(best_scores[article_id], 4)
            items.append(
                VectorSearchEnhanceItemDTO(
                    articleId=article_id,
                    vectorScore=score,
                    reason=self._generate_reason(score),
                    matchedChunks=chunks,
                )
            )

        items.sort(key=lambda item: item.vectorScore, reverse=True)
        self._logger.info(
            Messages.VECTOR_ENHANCE_SEARCH_SUCCESS(len(article_ids), len(items))
        )
        return VectorSearchEnhanceResp(items=items)

    def _normalize_article_ids(
        self, article_ids: list[int], req_limit: int
    ) -> list[int]:
        """对候选文章 ID 去重、过滤非法值，并按请求 limit 与候选上限截断"""
        limit = self.candidate_limit
        if req_limit > 0:
            limit = min(limit, req_limit)

        normalized: list[int] = []
        seen = set()
        for article_id in article_ids:
            aid = self._to_int(article_id)
            if aid is None or aid <= 0 or aid in seen:
                continue
            normalized.append(aid)
            seen.add(aid)
            if len(normalized) >= limit:
                break
        return normalized

    def _resolve_fetch_k(self, top_k: int, candidate_count: int) -> int:
        """按 topK、候选数与召回倍数计算向量检索的 fetch_k，并保证不小于最大命中片段数"""
        requested = top_k if top_k > 0 else candidate_count
        requested = min(max(requested, candidate_count), self.candidate_limit)
        return max(requested * self.fetch_multiplier, self.max_matched_chunks)

    def _build_query(self, keyword: str, req: VectorSearchEnhanceReq) -> str:
        """把关键词与分类、子分类、标签拼接为多行向量检索查询文本"""
        parts = [keyword]
        if req.categoryName:
            parts.append(Messages.VECTOR_QUERY_CATEGORY(req.categoryName))
        if req.subCategoryName:
            parts.append(Messages.VECTOR_QUERY_SUB_CATEGORY(req.subCategoryName))
        tags = [tag.strip() for tag in req.tags if tag and tag.strip()]
        if tags:
            parts.append(Messages.VECTOR_QUERY_TAGS(", ".join(tags[:10])))
        return "\n".join(parts)

    def _normalize_score(self, raw_score: float) -> float:
        """按 distance 或 similarity 模式把原始分数归一化到 0 到 1 区间"""
        if self.score_mode == "distance":
            score = 1 / (1 + max(raw_score, 0))
        else:
            score = raw_score
        return max(0.0, min(float(score), 1.0))

    def _generate_reason(self, score: float) -> str:
        """按语义相似度分数高低返回高、中、低三档推荐原因文案"""
        if score >= 0.8:
            return Messages.VECTOR_SEARCH_REASON_HIGH
        if score >= 0.6:
            return Messages.VECTOR_SEARCH_REASON_MEDIUM
        return Messages.VECTOR_SEARCH_REASON_LOW

    def _trim_content(self, content: str, max_length: int = 220) -> str:
        """压缩空白后把片段内容截断到指定长度并追加省略号"""
        text = " ".join((content or "").split())
        if len(text) <= max_length:
            return text
        return text[:max_length].rstrip() + "..."

    def _to_int(self, value: Any) -> int | None:
        """安全地把任意值转换为整数，转换失败返回 None"""
        try:
            return int(value)
        except (TypeError, ValueError):
            return None


@lru_cache
def get_vector_search_service(
    vector_mapper: Optional[VectorMapper] = None,
    logger: LoggerProtocol | None = None,
) -> VectorSearchService:
    """获取 VectorSearchService 单例"""
    return VectorSearchService(
        enabled=Defaults.VECTOR_SEARCH_ENABLED,
        candidate_limit=Defaults.VECTOR_SEARCH_CANDIDATE_LIMIT,
        fetch_multiplier=Defaults.VECTOR_SEARCH_FETCH_MULTIPLIER,
        max_matched_chunks=Defaults.VECTOR_SEARCH_MAX_MATCHED_CHUNKS,
        min_score=Defaults.VECTOR_SEARCH_MIN_SCORE,
        score_mode=Defaults.VECTOR_SEARCH_SCORE_MODE,
        vector_mapper=vector_mapper,
        logger=logger,
    )
