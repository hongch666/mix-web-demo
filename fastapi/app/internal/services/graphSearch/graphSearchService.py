from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Callable
from functools import lru_cache
from typing import Any

from app.core.base import Logger, LoggerProtocol
from app.core.constants import Defaults, Messages, Scripts
from app.core.db import get_neo4j_client
from app.internal.cache import (
    GraphCandidateCache,
    GraphSignalCache,
)
from app.internal.schemas import (
    GraphRelationDTO,
    GraphSearchEnhanceItemDTO,
    GraphSearchEnhanceReq,
    GraphSearchEnhanceResp,
)


class GraphSearchService:
    """图谱搜索增强服务"""

    def __init__(
        self,
        tag_interest_weight: float = 0.35,
        followed_author_weight: float = 0.25,
        same_sub_category_weight: float = 0.20,
        candidate_similarity_weight: float = 0.20,
        keyword_tag_weight: float = 0.20,
        candidate_limit: int = 200,
        logger: LoggerProtocol | None = None,
        signal_cache: GraphSignalCache | None = None,
        candidate_cache: GraphCandidateCache | None = None,
    ) -> None:
        """初始化五路图谱信号的权重、候选文章上限，并注入单文章信号缓存、批次候选缓存与日志器"""
        self.TAG_INTEREST_WEIGHT: float = tag_interest_weight
        self.FOLLOWED_AUTHOR_WEIGHT: float = followed_author_weight
        self.SAME_SUB_CATEGORY_WEIGHT: float = same_sub_category_weight
        self.CANDIDATE_SIMILARITY_WEIGHT: float = candidate_similarity_weight
        self.KEYWORD_TAG_WEIGHT: float = keyword_tag_weight
        self.candidate_limit: int = max(candidate_limit, 1)
        # 单文章信号缓存（信号1/2/3/5）与批次候选缓存（信号4）可注入，缺省时保持手工构造可用（不启用缓存）
        self._signal_cache: GraphSignalCache | None = signal_cache
        self._candidate_cache: GraphCandidateCache | None = candidate_cache
        # 日志器可注入，缺省回退全局单例
        self._logger: LoggerProtocol = logger or Logger

    async def enhance(self, req: GraphSearchEnhanceReq) -> GraphSearchEnhanceResp:
        """执行图谱增强, 返回候选文章的图谱分和推荐原因"""
        if not req.articleIds:
            return GraphSearchEnhanceResp()

        # 候选上限与 GoZero 侧召回上限对齐，请求未指定 limit 时按服务上限截断
        limit = (
            min(req.limit, self.candidate_limit)
            if req.limit > 0
            else self.candidate_limit
        )
        article_ids = req.articleIds[:limit]
        keyword = req.keyword[:100] if req.keyword else ""

        # 并行执行多个图谱信号查询
        tasks = []
        # 信号1: 用户兴趣标签 (需要 userId)
        if req.userId and req.userId > 0:
            tasks.append(self._query_tag_interest(req.userId, article_ids))
        else:
            tasks.append(self._empty_result(article_ids))

        # 信号2: 关注作者 (需要 userId)
        if req.userId and req.userId > 0:
            tasks.append(self._query_followed_author(req.userId, article_ids))
        else:
            tasks.append(self._empty_result(article_ids))

        # 信号3: 同子分类 (需要 userId)
        if req.userId and req.userId > 0:
            tasks.append(self._query_same_sub_category(req.userId, article_ids))
        else:
            tasks.append(self._empty_result(article_ids))

        # 信号4: 候选间相似标签
        tasks.append(self._query_candidate_similarity(article_ids))

        # 信号5: 关键词标签命中
        tasks.append(self._query_keyword_tag(article_ids, keyword))

        # 等待所有查询完成 (单个失败不影响其他)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 解析结果
        signal_results: list[dict[int, dict]] = []
        for raw in results:
            # gather 带 return_exceptions 时结果类型含 BaseException，异常分支单独降级为空结果
            signal_result: Any = raw
            if isinstance(signal_result, Exception):
                self._logger.warning(
                    Messages.GRAPH_SEARCH_QUERY_EXCEPTION_LOG(signal_result)
                )
                signal_results.append({})
            else:
                signal_results.append(signal_result)

        # 合并分数
        article_scores: dict[int, dict] = {}
        for article_id in article_ids:
            article_scores[article_id] = {
                "graphScore": 0.0,
                "relations": [],
                "matchedTags": [],
                "matchedPaths": [],
            }

        # 累加各信号分数
        for signal_result in signal_results:
            for article_id, data in signal_result.items():
                if article_id in article_scores:
                    base = article_scores[article_id]
                    base["graphScore"] = min(
                        base["graphScore"] + data.get("score", 0.0), 1.0
                    )
                    base["relations"].extend(data.get("relations", []))
                    base["matchedTags"].extend(data.get("matchedTags", []))
                    base["matchedPaths"].extend(data.get("matchedPaths", []))

        # 生成最终结果
        items = []
        sorted_ids = sorted(
            article_scores.keys(),
            key=lambda aid: article_scores[aid]["graphScore"],
            reverse=True,
        )

        for article_id in sorted_ids:
            data = article_scores[article_id]
            final_score = min(data["graphScore"], 1.0)
            if final_score < 0:
                final_score = 0.0

            reason = self._generate_reason(data["relations"])
            items.append(
                GraphSearchEnhanceItemDTO(
                    articleId=article_id,
                    graphScore=round(final_score, 4),
                    reason=reason,
                    relations=data["relations"],
                    matchedTags=data["matchedTags"],
                    matchedPaths=data["matchedPaths"],
                )
            )

        return GraphSearchEnhanceResp(items=items)

    async def _empty_result(self, article_ids: list[int]) -> dict[int, dict]:
        """空结果 (不依赖用户行为时使用)"""
        return {}

    async def _query_tag_interest(
        self, user_id: int, article_ids: list[int]
    ) -> dict[int, dict]:
        """信号1: 用户兴趣标签"""
        rows = await self._per_article_rows(
            {
                article_id: f"tag_interest:{article_id}:{user_id}"
                for article_id in article_ids
            },
            Scripts.GRAPH_SEARCH_TAG_INTEREST_CYPHER,
            lambda missing_ids: {"userId": user_id, "articleIds": missing_ids},
        )

        result: dict[int, dict] = {}
        for row in rows:
            aid = row.get("articleId")
            if aid is None:
                continue
            raw = row.get("rawScore", 0) or 0
            score = min(raw / 5.0, 1.0) * self.TAG_INTEREST_WEIGHT
            tags = row.get("matchedTags", []) or []
            result[aid] = {
                "score": score,
                "relations": [
                    GraphRelationDTO(
                        type="tag_interest",
                        name=tag,
                        score=round(score, 4),
                        reason=Messages.GRAPH_SEARCH_REASON_INTEREST,
                    )
                    for tag in tags
                ],
                "matchedTags": tags,
                "matchedPaths": [Messages.GRAPH_SEARCH_PATH_INTEREST],
            }
        return result

    async def _query_followed_author(
        self, user_id: int, article_ids: list[int]
    ) -> dict[int, dict]:
        """信号2: 关注作者"""
        rows = await self._per_article_rows(
            {
                article_id: f"followed_author:{article_id}:{user_id}"
                for article_id in article_ids
            },
            Scripts.GRAPH_SEARCH_FOLLOWED_AUTHOR_CYPHER,
            lambda missing_ids: {"userId": user_id, "articleIds": missing_ids},
        )

        result: dict[int, dict] = {}
        for row in rows:
            aid = row.get("articleId")
            if aid is None:
                continue
            names = row.get("names", []) or []
            result[aid] = {
                "score": self.FOLLOWED_AUTHOR_WEIGHT,
                "relations": [
                    GraphRelationDTO(
                        type="followed_author",
                        name=name,
                        score=self.FOLLOWED_AUTHOR_WEIGHT,
                        reason=Messages.GRAPH_SEARCH_REASON_FOLLOWED,
                    )
                    for name in names
                ],
                "matchedTags": [],
                "matchedPaths": [Messages.GRAPH_SEARCH_PATH_FOLLOWED],
            }
        return result

    async def _query_same_sub_category(
        self, user_id: int, article_ids: list[int]
    ) -> dict[int, dict]:
        """信号3: 同子分类"""
        rows = await self._per_article_rows(
            {
                article_id: f"same_sub_category:{article_id}:{user_id}"
                for article_id in article_ids
            },
            Scripts.GRAPH_SEARCH_SAME_SUB_CATEGORY_CYPHER,
            lambda missing_ids: {"userId": user_id, "articleIds": missing_ids},
        )

        result: dict[int, dict] = {}
        for row in rows:
            aid = row.get("articleId")
            if aid is None:
                continue
            raw = row.get("rawScore", 0) or 0
            score = min(raw / 5.0, 1.0) * self.SAME_SUB_CATEGORY_WEIGHT
            names = row.get("names", []) or []
            result[aid] = {
                "score": score,
                "relations": [
                    GraphRelationDTO(
                        type="same_sub_category",
                        name=name,
                        score=round(score, 4),
                        reason=Messages.GRAPH_SEARCH_REASON_SUB_CATEGORY,
                    )
                    for name in names
                ],
                "matchedTags": [],
                "matchedPaths": [Messages.GRAPH_SEARCH_PATH_SUB_CATEGORY],
            }
        return result

    async def _query_candidate_similarity(
        self, article_ids: list[int]
    ) -> dict[int, dict]:
        """信号4: 候选间相似标签（打分依赖整个候选集合，按批次键缓存）"""
        rows = await self._batch_rows(
            self._ids_cache_hash(article_ids),
            Scripts.GRAPH_SEARCH_CANDIDATE_SIMILARITY_CYPHER,
            {
                "articleIds": article_ids,
            },
        )

        result: dict[int, dict] = {}
        for row in rows:
            aid = row.get("articleId")
            if aid is None:
                continue
            raw = row.get("rawScore", 0) or 0
            score = min(raw / 3.0, 1.0) * self.CANDIDATE_SIMILARITY_WEIGHT
            names = row.get("names", []) or []
            result[aid] = {
                "score": score,
                "relations": [
                    GraphRelationDTO(
                        type="candidate_similarity",
                        name="候选共享标签",
                        score=round(score, 4),
                        reason=Messages.GRAPH_SEARCH_REASON_CANDIDATE,
                    )
                ],
                "matchedTags": names,
                "matchedPaths": [Messages.GRAPH_SEARCH_PATH_CANDIDATE],
            }
        return result

    async def _query_keyword_tag(
        self, article_ids: list[int], keyword: str
    ) -> dict[int, dict]:
        """信号5: 关键词标签命中"""
        if not keyword:
            return {}

        keyword_hash = hashlib.md5(keyword.encode()).hexdigest()
        rows = await self._per_article_rows(
            {
                article_id: f"keyword_tag:{article_id}:{keyword_hash}"
                for article_id in article_ids
            },
            Scripts.GRAPH_SEARCH_KEYWORD_TAG_CYPHER,
            lambda missing_ids: {
                "articleIds": missing_ids,
                "keyword": keyword,
            },
        )

        result: dict[int, dict] = {}
        for row in rows:
            aid = row.get("articleId")
            if aid is None:
                continue
            raw = row.get("rawScore", 0) or 0
            score = min(raw / 2.0, 1.0) * self.KEYWORD_TAG_WEIGHT
            names = row.get("names", []) or []
            result[aid] = {
                "score": score,
                "relations": [
                    GraphRelationDTO(
                        type="keyword_tag",
                        name=name,
                        score=round(score, 4),
                        reason=Messages.GRAPH_SEARCH_REASON_KEYWORD,
                    )
                    for name in names
                ],
                "matchedTags": names,
                "matchedPaths": [Messages.GRAPH_SEARCH_PATH_KEYWORD],
            }
        return result

    async def _per_article_rows(
        self,
        cache_keys: dict[int, str],
        cypher: str,
        build_params: Callable[[list[int]], dict],
    ) -> list[dict]:
        """按单文章键读取信号行：命中缓存的文章跳过查询，缺失的 id 合并为一次 Cypher 回源后逐篇回填

        查询失败时不回填缺失文章，避免把瞬时故障固化为长期缓存；
        与候选集组成相关的信号（候选间相似标签）不适用本方法，仍按批次键缓存
        """
        rows_by_id: dict[int, list[dict]] = {}
        missing_ids: list[int] = []

        if self._signal_cache is not None:
            for article_id, cache_key in cache_keys.items():
                cached_rows: list[dict] | None = await self._signal_cache.get_entry(
                    cache_key
                )
                if cached_rows is not None:
                    self._logger.info(Messages.GRAPH_SIGNAL_CACHE_HIT(cache_key))
                    rows_by_id[article_id] = cached_rows
                    continue
                missing_ids.append(article_id)
        else:
            missing_ids = list(cache_keys)

        if missing_ids:
            try:
                rows: list[dict] = await get_neo4j_client().run_query(
                    cypher, build_params(missing_ids), raise_on_error=True
                )
            except Exception as e:
                self._logger.warning(Messages.GRAPH_SEARCH_NEO4J_EXCEPTION_LOG(e))
                return self._flatten_rows(rows_by_id, cache_keys)

            grouped = self._group_rows_by_article(rows)
            for article_id in missing_ids:
                article_rows: list[dict] = grouped.get(article_id, [])
                rows_by_id[article_id] = article_rows
                if article_rows and self._signal_cache is not None:
                    await self._signal_cache.set_entry(
                        cache_keys[article_id], article_rows
                    )
                    self._logger.info(
                        Messages.GRAPH_SIGNAL_CACHE_STORED(
                            cache_keys[article_id], len(article_rows)
                        )
                    )

        return self._flatten_rows(rows_by_id, cache_keys)

    async def _batch_rows(self, ids_hash: str, cypher: str, params: dict) -> list[dict]:
        """按批次键读取信号行：优先命中候选缓存，未命中时回源查询并回填，空结果不缓存

        空结果不缓存：Neo4j 异常会被吞成空列表，缓存空集会把瞬时故障固化为长期缺失
        """
        cache_key = f"batch:{ids_hash}"
        if self._candidate_cache is not None:
            cached_rows: list[dict] | None = await self._candidate_cache.get_entry(
                cache_key
            )
            if cached_rows is not None:
                self._logger.info(Messages.GRAPH_SIGNAL_CACHE_HIT(cache_key))
                return cached_rows

        rows = await self._safe_query(cypher, params)
        if rows and self._candidate_cache is not None:
            await self._candidate_cache.set_entry(cache_key, rows)
            self._logger.info(Messages.GRAPH_SIGNAL_CACHE_STORED(cache_key, len(rows)))
        return rows

    @staticmethod
    def _group_rows_by_article(rows: list[dict]) -> dict[int, list[dict]]:
        """按行内的 articleId 把查询行分组，缺失或非法的 articleId 行被丢弃"""
        grouped: dict[int, list[dict]] = {}
        for row in rows:
            article_id = row.get("articleId")
            if article_id is None:
                continue
            try:
                grouped.setdefault(int(article_id), []).append(row)
            except (TypeError, ValueError):
                continue
        return grouped

    @staticmethod
    def _flatten_rows(
        rows_by_id: dict[int, list[dict]], cache_keys: dict[int, str]
    ) -> list[dict]:
        """按请求的文章顺序把分组行还原为原始行列表"""
        result: list[dict] = []
        for article_id in cache_keys:
            result.extend(rows_by_id.get(article_id, []))
        return result

    @staticmethod
    def _ids_cache_hash(article_ids: list[int]) -> str:
        """对文章 ID 集合做顺序无关的 md5，作为批次缓存键的参数部分"""
        joined = ",".join(str(aid) for aid in sorted(set(article_ids)))
        return hashlib.md5(joined.encode()).hexdigest()

    async def _safe_query(self, cypher: str, params: dict) -> list[dict]:
        """安全执行 Neo4j 查询, 失败时返回空列表"""
        try:
            neo4j = get_neo4j_client()
            return await neo4j.run_query(cypher, params)
        except Exception as e:
            self._logger.warning(Messages.GRAPH_SEARCH_NEO4J_EXCEPTION_LOG(e))
            return []

    def _generate_reason(self, relations: list[GraphRelationDTO]) -> str:
        """根据关系优先级生成推荐原因"""
        priority_map = {
            "followed_author": ("来自你关注的作者 {name}", 1),
            "tag_interest": ("与你最近点赞/收藏过的标签 {name} 相似", 2),
            "same_sub_category": ("属于你常看的分类 {name}", 3),
            "keyword_tag": ("命中图谱标签 {name}", 4),
            "candidate_similarity": (Messages.GRAPH_SEARCH_REASON_CANDIDATE, 5),
        }

        # 按优先级排序, 取最高优先级
        best = None
        best_priority = 999

        for rel in relations:
            if rel.type in priority_map:
                template, priority = priority_map[rel.type]
                if priority < best_priority:
                    best_priority = priority
                    best = (
                        template.format(name=rel.name)
                        if "{name}" in template
                        else template
                    )

        if best:
            return best

        # 兜底: 如果只有候选相似标签
        for rel in relations:
            if rel.type == "candidate_similarity":
                return Messages.GRAPH_SEARCH_REASON_CANDIDATE

        return ""


@lru_cache
def get_graph_search_service(
    logger: LoggerProtocol | None = None,
    signal_cache: GraphSignalCache | None = None,
    candidate_cache: GraphCandidateCache | None = None,
) -> GraphSearchService:
    """获取 GraphSearchService 单例"""
    return GraphSearchService(
        tag_interest_weight=Defaults.GRAPH_TAG_INTEREST_WEIGHT,
        followed_author_weight=Defaults.GRAPH_FOLLOWED_AUTHOR_WEIGHT,
        same_sub_category_weight=Defaults.GRAPH_SAME_SUB_CATEGORY_WEIGHT,
        candidate_similarity_weight=Defaults.GRAPH_CANDIDATE_SIMILARITY_WEIGHT,
        keyword_tag_weight=Defaults.GRAPH_KEYWORD_TAG_WEIGHT,
        candidate_limit=Defaults.GRAPH_SEARCH_CANDIDATE_LIMIT,
        logger=logger,
        signal_cache=signal_cache,
        candidate_cache=candidate_cache,
    )
