from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any, Dict, List, Tuple

from app.core.base import Logger
from app.core.config import load_config
from app.core.constants import Messages
from app.internal.agents import get_rag_tools
from app.internal.schemas.vectorSearchDTO import (
    VectorMatchedChunkDTO,
    VectorSearchEnhanceItemDTO,
    VectorSearchEnhanceReq,
    VectorSearchEnhanceResp,
)
from langchain_core.documents import Document

DocScore = Tuple[Document, float]


class VectorSearchService:
    """向量搜索增强服务"""

    def __init__(
        self,
        enabled: bool = True,
        candidate_limit: int = 50,
        fetch_multiplier: int = 4,
        max_matched_chunks: int = 2,
        min_score: float = 0.3,
        score_mode: str = "similarity",
    ) -> None:
        self.enabled = enabled
        self.candidate_limit = max(candidate_limit, 1)
        self.fetch_multiplier = max(fetch_multiplier, 1)
        self.max_matched_chunks = max(max_matched_chunks, 1)
        self.min_score = min_score
        self.score_mode = (
            score_mode if score_mode in {"similarity", "distance"} else "similarity"
        )

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

        rag_tools = get_rag_tools()
        docs_with_scores = await asyncio.to_thread(
            rag_tools.vector_store.similarity_search_with_score,
            query,
            fetch_k,
        )

        article_id_set = set(article_ids)
        grouped_chunks: Dict[int, List[VectorMatchedChunkDTO]] = {}
        best_scores: Dict[int, float] = {}

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
        Logger.info(
            f"向量搜索增强成功，候选 {len(article_ids)} 篇，命中 {len(items)} 篇"
        )
        return VectorSearchEnhanceResp(items=items)

    def _normalize_article_ids(
        self, article_ids: List[int], req_limit: int
    ) -> List[int]:
        limit = self.candidate_limit
        if req_limit > 0:
            limit = min(limit, req_limit)

        normalized: List[int] = []
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
        requested = top_k if top_k > 0 else candidate_count
        requested = min(max(requested, candidate_count), self.candidate_limit)
        return max(requested * self.fetch_multiplier, self.max_matched_chunks)

    def _build_query(self, keyword: str, req: VectorSearchEnhanceReq) -> str:
        parts = [keyword]
        if req.categoryName:
            parts.append(f"分类: {req.categoryName}")
        if req.subCategoryName:
            parts.append(f"子分类: {req.subCategoryName}")
        tags = [tag.strip() for tag in req.tags if tag and tag.strip()]
        if tags:
            parts.append("标签: " + ", ".join(tags[:10]))
        return "\n".join(parts)

    def _normalize_score(self, raw_score: float) -> float:
        if self.score_mode == "distance":
            score = 1 / (1 + max(raw_score, 0))
        else:
            score = raw_score
        return max(0.0, min(float(score), 1.0))

    def _generate_reason(self, score: float) -> str:
        if score >= 0.8:
            return Messages.VECTOR_SEARCH_REASON_HIGH
        if score >= 0.6:
            return Messages.VECTOR_SEARCH_REASON_MEDIUM
        return Messages.VECTOR_SEARCH_REASON_LOW

    def _trim_content(self, content: str, max_length: int = 220) -> str:
        text = " ".join((content or "").split())
        if len(text) <= max_length:
            return text
        return text[:max_length].rstrip() + "..."

    def _to_int(self, value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None


def _to_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y", "on"}


@lru_cache
def get_vector_search_service() -> VectorSearchService:
    """获取 VectorSearchService 单例（从配置读取参数）"""
    vector_search_cfg = (load_config("agent") or {}).get("vector_search", {})
    return VectorSearchService(
        enabled=_to_bool(vector_search_cfg.get("enabled"), True),
        candidate_limit=int(vector_search_cfg.get("candidate_limit", 50)),
        fetch_multiplier=int(vector_search_cfg.get("fetch_multiplier", 4)),
        max_matched_chunks=int(vector_search_cfg.get("max_matched_chunks", 2)),
        min_score=float(vector_search_cfg.get("min_score", 0.3)),
        score_mode=str(vector_search_cfg.get("score_mode", "similarity")),
    )
