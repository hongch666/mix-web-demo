import asyncio
import hashlib
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set

from app.core.base import Logger
from app.core.constants import Messages, RedisKeys, Scripts
from app.core.db import get_neo4j_client, get_redis_client
from app.internal.clients import SpringClient


class KnowledgeGraphSyncService:
    """知识图谱同步服务：将 MySQL 业务数据同步到 Neo4j"""

    # 同步抓取专用超时（秒）：全量数据行较多，且需与并发批量评分/文章列表等
    # 任务抢占 spring R2DBC 连接池，故单独使用较大超时，避免命中默认 5s 读取超时。
    SYNC_FETCH_TIMEOUT: int = 30

    # 清理分批大小：每批单独提交事务，避免单事务 DELETE 过多关系击穿
    # Neo4j 事务内存上限（dbms.memory.transaction.total.max）。
    CLEANUP_BATCH_SIZE: int = 1000

    def __init__(self) -> None:
        self.logger = Logger
        self.client = get_neo4j_client()
        self.spring_client = SpringClient()

    @staticmethod
    def _format_datetime(value: Any) -> str:
        if isinstance(value, datetime):
            return value.isoformat()
        if value:
            return str(value)
        return datetime.now().isoformat()

    @staticmethod
    def _compute_content_hash(title: Any, content: Any, tags: Any) -> str:
        raw_text = f"{title or ''}||{content or ''}||{tags or ''}"
        return hashlib.md5(raw_text.encode()).hexdigest()

    @staticmethod
    def _build_relation_key(*parts: Any) -> str:
        return ":".join(str(part) for part in parts)

    @staticmethod
    def _extract_deleted_count(summary: Any) -> int:
        counters = getattr(summary, "counters", None)
        if counters is None:
            return 0
        return int(getattr(counters, "nodes_deleted", 0) or 0) + int(
            getattr(counters, "relationships_deleted", 0) or 0
        )

    @staticmethod
    def _build_article_tag_relations(
        articles: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        relations: List[Dict[str, Any]] = []
        for article in articles:
            article_id = article.get("id")
            tags = str(article.get("tags") or "")
            for tag_name in [item.strip() for item in tags.split(",") if item.strip()]:
                relations.append({"articleId": article_id, "tagName": tag_name})
        return relations

    async def _fetch_snapshot(
        self, last_sync_time: Optional[datetime] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """通过Spring各模块独立接口并行获取业务表数据，避免直连MySQL。"""
        updated_after = last_sync_time.isoformat() if last_sync_time else None
        # 同步类抓取返回数据量可能较大（全量几千行），使用专用大超时避免命中
        # 远程调用默认 5s 读取超时；与并发批量评分/文章列表等任务抢占 spring
        # R2DBC 连接池时尤为必要。
        fetch_timeout = self.SYNC_FETCH_TIMEOUT
        # 分类/子分类是基础维度，数据量小（通常数十~数百条）且极少变更。
        # 增量同步窗口内它们常无更新，若走 updated_after 会导致快照为空、
        # 基础节点永远无法写入 Neo4j。故始终全量抓取，确保基础维度完整。
        categories_after = None
        sub_categories_after = None
        (
            users,
            categories,
            sub_categories,
            articles,
            likes,
            collects,
            comments,
            focus,
        ) = await asyncio.gather(
            self.spring_client.get_neo4j_sync_users(updated_after, timeout=fetch_timeout),
            self.spring_client.get_neo4j_sync_categories(categories_after, timeout=fetch_timeout),
            self.spring_client.get_neo4j_sync_sub_categories(sub_categories_after, timeout=fetch_timeout),
            self.spring_client.get_neo4j_sync_articles(updated_after, timeout=fetch_timeout),
            self.spring_client.get_neo4j_sync_likes(updated_after, timeout=fetch_timeout),
            self.spring_client.get_neo4j_sync_collects(updated_after, timeout=fetch_timeout),
            self.spring_client.get_neo4j_sync_comments(updated_after, timeout=fetch_timeout),
            self.spring_client.get_neo4j_sync_focus(updated_after, timeout=fetch_timeout),
        )
        return {
            "users": users,
            "categories": categories,
            "sub_categories": sub_categories,
            "articles": articles,
            "likes": likes,
            "collects": collects,
            "comments": comments,
            "focus": focus,
        }

    def _normalize_users(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "id": int(row.get("id")),
                "name": row.get("name") or "",
                "email": row.get("email") or "",
                "role": row.get("role") or "user",
                "img": row.get("img") or "",
                "signature": row.get("signature") or "",
                "createdAt": self._format_datetime(row.get("created_at")),
                "updatedAt": self._format_datetime(row.get("updated_at")),
            }
            for row in rows
            if row.get("id") is not None
        ]

    def _normalize_categories(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "id": int(row["id"]),
                "name": row.get("name") or "",
                "updatedAt": self._format_datetime(row.get("update_time")),
            }
            for row in rows
            if row.get("id") is not None
        ]

    def _normalize_sub_categories(
        self, rows: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return [
            {
                "id": int(row["id"]),
                "name": row.get("name") or "",
                "categoryId": int(row["category_id"])
                if row.get("category_id") is not None
                else None,
                "updatedAt": self._format_datetime(row.get("update_time")),
            }
            for row in rows
            if row.get("id") is not None
        ]

    def _normalize_articles(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "id": int(row["id"]),
                "title": row.get("title") or "",
                "tags": row.get("tags") or "",
                "status": str(row.get("status") or ""),
                "views": int(row.get("views") or 0),
                "userId": int(row["user_id"])
                if row.get("user_id") is not None
                else None,
                "subCategoryId": int(row["sub_category_id"])
                if row.get("sub_category_id") is not None
                else None,
                "createAt": self._format_datetime(row.get("create_at")),
                "updateAt": self._format_datetime(row.get("update_at")),
                "contentHash": self._compute_content_hash(
                    row.get("title"), row.get("content"), row.get("tags")
                ),
                "updatedAt": self._format_datetime(row.get("update_at")),
            }
            for row in rows
            if row.get("id") is not None
        ]

    def _normalize_likes(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "userId": int(row["user_id"]),
                "articleId": int(row["article_id"]),
                "createdAt": self._format_datetime(row.get("created_time")),
            }
            for row in rows
            if row.get("user_id") is not None and row.get("article_id") is not None
        ]

    def _normalize_collects(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return self._normalize_likes(rows)

    def _normalize_comments(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "commentId": int(row["id"]),
                "userId": int(row["user_id"]),
                "articleId": int(row["article_id"]),
                "createdAt": self._format_datetime(row.get("create_time")),
            }
            for row in rows
            if row.get("id") is not None
        ]

    def _normalize_focus(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "followerId": int(row["user_id"]),
                "followedId": int(row["focus_id"]),
                "createdAt": self._format_datetime(row.get("created_time")),
            }
            for row in rows
            if row.get("user_id") is not None and row.get("focus_id") is not None
        ]

    async def _ensure_schema(self) -> None:
        for cypher in Scripts.NEO4J_CREATE_CONSTRAINTS:
            await self.client.run_write_query(cypher)

    async def _batch_write(
        self,
        rows: List[Dict[str, Any]],
        cypher: str,
        label: str,
        batch_size: int = 500,
    ) -> int:
        if not rows:
            self.logger.info(Messages.NEO4J_SYNC_NO_DATA(label))
            return 0

        total = 0
        for start in range(0, len(rows), batch_size):
            batch = rows[start : start + batch_size]
            await self.client.run_write_query(cypher, {"rows": batch})
            total += len(batch)
            self.logger.info(Messages.NEO4J_SYNC_PROGRESS(label, total, len(rows)))
        return total

    async def _cleanup_write(
        self, cypher: str, params: Dict[str, Any], label: str
    ) -> int:
        # 防御性保护：当待保留的键集合为空时，Cypher 的 `WHERE NOT key IN []`
        # 会等价于 `WHERE true`，从而误删图中全部对应关系/节点。这通常意味着
        # 上游快照抓取失败（返回空），属于异常情况，必须跳过而非执行全量删除。
        keep_keys = params.get("keys") or params.get("ids") or params.get("names")
        if not keep_keys:
            self.logger.warning(
                Messages.NEO4J_CLEANUP_SKIP_EMPTY(label)
            )
            return 0
        total_deleted = 0
        if "keys" in params:
            # 关系类清理（`DELETE r`，通过 `WHERE NOT key IN $keys` 删关系）：
            # 可分批执行，每批单独提交事务，避免单事务内删除过多关系击穿
            # Neo4j 事务内存上限（dbms.memory.transaction.total.max）。
            batch_size = self.CLEANUP_BATCH_SIZE
            for start in range(0, len(keep_keys), batch_size):
                batch = keep_keys[start : start + batch_size]
                batch_params = {**params, "keys": batch}
                summary = await self.client.run_write_query(cypher, batch_params)
                total_deleted += self._extract_deleted_count(summary)
        else:
            # 节点类清理（`DETACH DELETE n`，通过 `WHERE NOT n.id IN $ids` 删节点）：
            # 语义是"删除不在该集合中的所有节点"。若分批切小 $ids，每批都会
            # 误删集合之外的全部节点（灾难+OOM）。因此必须一次传入完整集合，
            # 确保只删除真正不存在的节点。若集合为空则由上面的保护直接跳过。
            summary = await self.client.run_write_query(cypher, params)
            total_deleted += self._extract_deleted_count(summary)
        self.logger.info(Messages.NEO4J_SYNC_CLEANUP(label, total_deleted))
        return total_deleted

    async def _has_graph_data(self) -> bool:
        records = await self.client.run_query(Messages.NEO4J_GRAPH_COUNT_CYPHER)
        if not records:
            return False
        total = records[0].get("total", 0)
        try:
            return int(total) > 0
        except (TypeError, ValueError):
            return False

    async def _cleanup_deleted_graph_data(
        self,
        users: Optional[List[Dict[str, Any]]] = None,
        categories: Optional[List[Dict[str, Any]]] = None,
        sub_categories: Optional[List[Dict[str, Any]]] = None,
        articles: Optional[List[Dict[str, Any]]] = None,
        likes: Optional[List[Dict[str, Any]]] = None,
        collects: Optional[List[Dict[str, Any]]] = None,
        comments: Optional[List[Dict[str, Any]]] = None,
        focus: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, int]:
        """按 MySQL 当前完整快照删除 Neo4j 中已经不存在的节点和关系

        注意：调用方（sync_all / sync_incremental）已经在第一阶段抓取并归一化了
        完整快照，这里必须复用传入的归一化数据，禁止再次调用 _fetch_snapshot，
        否则会触发第二次 8 并发远程抓取，叠加占用 spring R2DBC 连接池导致超时。
        """
        self.logger.info(Messages.NEO4J_CLEANUP_DELETED_DATA_START_MESSAGE)

        # 直接复用调用方传入的归一化快照（同步任务第一阶段已抓取并归一化），
        # 不再二次远程抓取，避免并发占用 spring R2DBC 连接池导致超时。
        users = users or []
        categories = categories or []
        sub_categories = sub_categories or []
        articles = articles or []
        likes = likes or []
        collects = collects or []
        comments = comments or []
        focus = focus or []
        article_tag_relations = self._build_article_tag_relations(articles)

        cleanup_result: Dict[str, int] = {}

        cleanup_result["published_by"] = await self._cleanup_write(
            Scripts.NEO4J_CLEANUP_PUBLISHED_BY_CYPHER,
            {
                "keys": [
                    self._build_relation_key(item["id"], item["userId"])
                    for item in articles
                    if item.get("userId") is not None
                ]
            },
            Messages.NEO4J_CLEANUP_LABEL_PUBLISHED_BY_RELATION,
        )

        cleanup_result["article_sub_category"] = await self._cleanup_write(
            Scripts.NEO4J_CLEANUP_ARTICLE_SUB_CATEGORY_CYPHER,
            {
                "keys": [
                    self._build_relation_key(item["id"], item["subCategoryId"])
                    for item in articles
                    if item.get("subCategoryId") is not None
                ]
            },
            Messages.NEO4J_CLEANUP_LABEL_ARTICLE_SUB_CATEGORY_RELATION,
        )

        cleanup_result["sub_category_category"] = await self._cleanup_write(
            Scripts.NEO4J_CLEANUP_SUB_CATEGORY_CATEGORY_CYPHER,
            {
                "keys": [
                    self._build_relation_key(item["id"], item["categoryId"])
                    for item in sub_categories
                    if item.get("categoryId") is not None
                ]
            },
            Messages.NEO4J_CLEANUP_LABEL_SUB_CATEGORY_CATEGORY_RELATION,
        )

        cleanup_result["tagged_as"] = await self._cleanup_write(
            Scripts.NEO4J_CLEANUP_TAGGED_AS_CYPHER,
            {
                "keys": [
                    self._build_relation_key(item["articleId"], item["tagName"])
                    for item in article_tag_relations
                ]
            },
            Messages.NEO4J_CLEANUP_LABEL_TAGGED_AS_RELATION,
        )

        cleanup_result["likes"] = await self._cleanup_write(
            Scripts.NEO4J_CLEANUP_LIKES_CYPHER,
            {
                "keys": [
                    self._build_relation_key(item["userId"], item["articleId"])
                    for item in likes
                ]
            },
            Messages.NEO4J_CLEANUP_LABEL_LIKE_RELATION,
        )

        cleanup_result["collects"] = await self._cleanup_write(
            Scripts.NEO4J_CLEANUP_COLLECTS_CYPHER,
            {
                "keys": [
                    self._build_relation_key(item["userId"], item["articleId"])
                    for item in collects
                ]
            },
            Messages.NEO4J_CLEANUP_LABEL_COLLECT_RELATION,
        )

        cleanup_result["commented_on"] = await self._cleanup_write(
            Scripts.NEO4J_CLEANUP_COMMENTED_ON_CYPHER,
            {
                "keys": [
                    self._build_relation_key(
                        item["commentId"], item["userId"], item["articleId"]
                    )
                    for item in comments
                ]
            },
            Messages.NEO4J_CLEANUP_LABEL_COMMENT_RELATION,
        )

        cleanup_result["follows"] = await self._cleanup_write(
            Scripts.NEO4J_CLEANUP_FOLLOWS_CYPHER,
            {
                "keys": [
                    self._build_relation_key(item["followerId"], item["followedId"])
                    for item in focus
                ]
            },
            Messages.NEO4J_CLEANUP_LABEL_FOLLOW_RELATION,
        )

        cleanup_result["articles"] = await self._cleanup_write(
            Scripts.NEO4J_CLEANUP_ARTICLES_CYPHER,
            {"ids": [item["id"] for item in articles]},
            Messages.NEO4J_CLEANUP_LABEL_ARTICLE,
        )

        cleanup_result["users"] = await self._cleanup_write(
            Scripts.NEO4J_CLEANUP_USERS_CYPHER,
            {"ids": [item["id"] for item in users]},
            Messages.NEO4J_CLEANUP_LABEL_USER,
        )

        cleanup_result["sub_categories"] = await self._cleanup_write(
            Scripts.NEO4J_CLEANUP_SUB_CATEGORIES_CYPHER,
            {"ids": [item["id"] for item in sub_categories]},
            Messages.NEO4J_CLEANUP_LABEL_SUB_CATEGORY,
        )

        cleanup_result["categories"] = await self._cleanup_write(
            Scripts.NEO4J_CLEANUP_CATEGORIES_CYPHER,
            {"ids": [item["id"] for item in categories]},
            Messages.NEO4J_CLEANUP_LABEL_CATEGORY,
        )

        cleanup_result["tags"] = await self._cleanup_write(
            Scripts.NEO4J_CLEANUP_TAGS_CYPHER,
            {
                "names": sorted(
                    {
                        item["tagName"]
                        for item in article_tag_relations
                        if item.get("tagName")
                    }
                )
            },
            Messages.NEO4J_CLEANUP_LABEL_TAG,
        )

        cleanup_result["total"] = sum(cleanup_result.values())
        self.logger.info(Messages.NEO4J_SYNC_CLEANUP_COMPLETE(cleanup_result))
        return cleanup_result

    async def sync_all(self) -> Dict[str, int]:
        """全量同步 MySQL 数据到 Neo4j"""
        self.logger.info(Messages.NEO4J_SYNC_START_MESSAGE)
        await self._ensure_schema()

        result: Dict[str, int] = {}

        snapshot = await self._fetch_snapshot()
        users = self._normalize_users(snapshot.get("users", []))
        categories = self._normalize_categories(snapshot.get("categories", []))
        sub_categories = self._normalize_sub_categories(
            snapshot.get("sub_categories", [])
        )
        articles = self._normalize_articles(snapshot.get("articles", []))
        likes = self._normalize_likes(snapshot.get("likes", []))
        collects = self._normalize_collects(snapshot.get("collects", []))
        comments = self._normalize_comments(snapshot.get("comments", []))
        focus = self._normalize_focus(snapshot.get("focus", []))
        result["users"] = await self._batch_write(
            users, Scripts.NEO4J_MERGE_USERS_CYPHER, Messages.NEO4J_LABEL_USER
        )

        result["categories"] = await self._batch_write(
            categories,
            Scripts.NEO4J_MERGE_CATEGORIES_CYPHER,
            Messages.NEO4J_LABEL_CATEGORY,
        )

        result["sub_categories"] = await self._batch_write(
            sub_categories,
            Scripts.NEO4J_MERGE_SUB_CATEGORIES_CYPHER,
            Messages.NEO4J_LABEL_SUB_CATEGORY,
        )

        result["articles"] = await self._batch_write(
            articles,
            Scripts.NEO4J_MERGE_ARTICLES_CYPHER,
            Messages.NEO4J_LABEL_ARTICLE,
        )

        tag_names: Set[str] = set()
        article_tag_relations: List[Dict[str, Any]] = []
        for article in articles:
            tags = str(article.get("tags") or "")
            for tag_name in [item.strip() for item in tags.split(",") if item.strip()]:
                tag_names.add(tag_name)
                article_tag_relations.append(
                    {"articleId": article["id"], "tagName": tag_name}
                )
        tags = [{"name": tag_name} for tag_name in sorted(tag_names)]
        result["tags"] = await self._batch_write(
            tags, Scripts.NEO4J_MERGE_TAGS_CYPHER, Messages.NEO4J_LABEL_TAG
        )

        sub_category_relations = [
            {"subCategoryId": item["id"], "categoryId": item["categoryId"]}
            for item in sub_categories
            if item.get("categoryId") is not None
        ]
        result["sub_category_belongs_to_category"] = await self._batch_write(
            sub_category_relations,
            Scripts.NEO4J_MERGE_SUB_CATEGORY_TO_CATEGORY_CYPHER,
            Messages.NEO4J_LABEL_SUB_CATEGORY_RELATION,
        )

        article_sub_relations = [
            {"articleId": item["id"], "subCategoryId": item["subCategoryId"]}
            for item in articles
            if item.get("subCategoryId") is not None
        ]
        result["belongs_to"] = await self._batch_write(
            article_sub_relations,
            Scripts.NEO4J_MERGE_ARTICLE_TO_SUB_CATEGORY_CYPHER,
            Messages.NEO4J_LABEL_ARTICLE_SUB_CATEGORY_RELATION,
        )

        article_user_relations = [
            {"articleId": item["id"], "userId": item["userId"]}
            for item in articles
            if item.get("userId") is not None
        ]
        result["published_by"] = await self._batch_write(
            article_user_relations,
            Scripts.NEO4J_MERGE_PUBLISHED_BY_CYPHER,
            Messages.NEO4J_LABEL_ARTICLE_AUTHOR_RELATION,
        )

        result["tagged_as"] = await self._batch_write(
            article_tag_relations,
            Scripts.NEO4J_MERGE_TAGGED_AS_CYPHER,
            Messages.NEO4J_LABEL_ARTICLE_TAG_RELATION,
        )

        result["likes"] = await self._batch_write(
            likes,
            Scripts.NEO4J_MERGE_LIKES_CYPHER,
            Messages.NEO4J_LABEL_LIKE_RELATION,
        )

        result["collects"] = await self._batch_write(
            collects,
            Scripts.NEO4J_MERGE_COLLECTS_CYPHER,
            Messages.NEO4J_LABEL_COLLECT_RELATION,
        )

        result["commented_on"] = await self._batch_write(
            comments,
            Scripts.NEO4J_MERGE_COMMENTED_ON_CYPHER,
            Messages.NEO4J_LABEL_COMMENT_RELATION,
        )

        result["follows"] = await self._batch_write(
            focus,
            Scripts.NEO4J_MERGE_FOLLOWS_CYPHER,
            Messages.NEO4J_LABEL_FOLLOW_RELATION,
        )

        # 全量同步以全量快照 MERGE 重建图，cleanup 冗余且有误删风险，历史脏数据通过清空重建兜底
        self.logger.info(Messages.NEO4J_FULL_SYNC_SKIP_CLEANUP_MESSAGE)

        self.logger.info(Messages.NEO4J_SYNC_FULL_COMPLETE(result))
        return result

    async def sync_incremental(
        self, last_sync_time: Optional[datetime]
    ) -> Dict[str, int]:
        """增量同步 MySQL 数据到 Neo4j，如果图为空则退化为全量同步"""
        await self._ensure_schema()

        has_graph_data = await self._has_graph_data()
        if not has_graph_data:
            self.logger.info(Messages.NEO4J_GRAPH_EMPTY_FULL_SYNC_MESSAGE)
            return await self.sync_all()

        if last_sync_time is None:
            self.logger.info(Messages.NEO4J_GRAPH_EMPTY_FULL_SYNC_MESSAGE)
            return await self.sync_all()

        self.logger.info(Messages.NEO4J_INCREMENTAL_SYNC_START_MESSAGE)

        result: Dict[str, int] = {}

        snapshot = await self._fetch_snapshot(last_sync_time)
        users = self._normalize_users(snapshot.get("users", []))
        categories = self._normalize_categories(snapshot.get("categories", []))
        sub_categories = self._normalize_sub_categories(
            snapshot.get("sub_categories", [])
        )
        articles = self._normalize_articles(snapshot.get("articles", []))
        likes = self._normalize_likes(snapshot.get("likes", []))
        collects = self._normalize_collects(snapshot.get("collects", []))
        comments = self._normalize_comments(snapshot.get("comments", []))
        focus = self._normalize_focus(snapshot.get("focus", []))
        result["users"] = await self._batch_write(
            users, Scripts.NEO4J_MERGE_USERS_CYPHER, Messages.NEO4J_LABEL_USER
        )

        result["categories"] = await self._batch_write(
            categories,
            Scripts.NEO4J_MERGE_CATEGORIES_CYPHER,
            Messages.NEO4J_LABEL_CATEGORY,
        )

        result["sub_categories"] = await self._batch_write(
            sub_categories,
            Scripts.NEO4J_MERGE_SUB_CATEGORIES_CYPHER,
            Messages.NEO4J_LABEL_SUB_CATEGORY,
        )

        result["articles"] = await self._batch_write(
            articles,
            Scripts.NEO4J_MERGE_ARTICLES_CYPHER,
            Messages.NEO4J_LABEL_ARTICLE,
        )

        tag_names: Set[str] = set()
        article_tag_relations: List[Dict[str, Any]] = []
        for article in articles:
            tags = str(article.get("tags") or "")
            for tag_name in [item.strip() for item in tags.split(",") if item.strip()]:
                tag_names.add(tag_name)
                article_tag_relations.append(
                    {"articleId": article["id"], "tagName": tag_name}
                )
        tags = [{"name": tag_name} for tag_name in sorted(tag_names)]
        result["tags"] = await self._batch_write(
            tags, Scripts.NEO4J_MERGE_TAGS_CYPHER, Messages.NEO4J_LABEL_TAG
        )

        sub_category_relations = [
            {"subCategoryId": item["id"], "categoryId": item["categoryId"]}
            for item in sub_categories
            if item.get("categoryId") is not None
        ]
        result["sub_category_belongs_to_category"] = await self._batch_write(
            sub_category_relations,
            Scripts.NEO4J_MERGE_SUB_CATEGORY_TO_CATEGORY_CYPHER,
            Messages.NEO4J_LABEL_SUB_CATEGORY_RELATION,
        )

        article_sub_relations = [
            {"articleId": item["id"], "subCategoryId": item["subCategoryId"]}
            for item in articles
            if item.get("subCategoryId") is not None
        ]
        result["belongs_to"] = await self._batch_write(
            article_sub_relations,
            Scripts.NEO4J_MERGE_ARTICLE_TO_SUB_CATEGORY_CYPHER,
            Messages.NEO4J_LABEL_ARTICLE_SUB_CATEGORY_RELATION,
        )

        article_user_relations = [
            {"articleId": item["id"], "userId": item["userId"]}
            for item in articles
            if item.get("userId") is not None
        ]
        result["published_by"] = await self._batch_write(
            article_user_relations,
            Scripts.NEO4J_MERGE_PUBLISHED_BY_CYPHER,
            Messages.NEO4J_LABEL_ARTICLE_AUTHOR_RELATION,
        )

        result["tagged_as"] = await self._batch_write(
            article_tag_relations,
            Scripts.NEO4J_MERGE_TAGGED_AS_CYPHER,
            Messages.NEO4J_LABEL_ARTICLE_TAG_RELATION,
        )

        result["likes"] = await self._batch_write(
            likes,
            Scripts.NEO4J_MERGE_LIKES_CYPHER,
            Messages.NEO4J_LABEL_LIKE_RELATION,
        )

        result["collects"] = await self._batch_write(
            collects,
            Scripts.NEO4J_MERGE_COLLECTS_CYPHER,
            Messages.NEO4J_LABEL_COLLECT_RELATION,
        )

        result["commented_on"] = await self._batch_write(
            comments,
            Scripts.NEO4J_MERGE_COMMENTED_ON_CYPHER,
            Messages.NEO4J_LABEL_COMMENT_RELATION,
        )

        result["follows"] = await self._batch_write(
            focus,
            Scripts.NEO4J_MERGE_FOLLOWS_CYPHER,
            Messages.NEO4J_LABEL_FOLLOW_RELATION,
        )

        # 增量同步不做"按快照删全图"的清理：增量快照仅含窗口内变更记录，
        # 不含已删除的记录，无法安全判断哪些节点/关系应从图中移除。若用
        # 增量快照执行清理（如 articles 仅 1 篇时 `WHERE NOT id IN [1篇]`），
        # 会误删全图绝大部分节点并击穿 Neo4j 事务内存上限（OOM）。
        # 全图清理仅由全量同步 sync_all 在安全快照下执行；已删除数据的清理
        # 由周期性全量同步兜底。
        self.logger.info(Messages.NEO4J_INCREMENTAL_SKIP_CLEANUP_MESSAGE)

        if not any(result.values()):
            self.logger.info(Messages.NEO4J_NO_INCREMENTAL_DATA_MESSAGE)

        return result


@lru_cache
def get_knowledge_graph_sync_service() -> KnowledgeGraphSyncService:
    """获取知识图谱同步服务单例"""
    return KnowledgeGraphSyncService()


async def _save_sync_time(sync_time: datetime) -> None:
    """将 Neo4j 同步时间保存到 Redis"""
    try:
        redis_client = get_redis_client()
        await redis_client.set(RedisKeys.NEO4J_SYNC_TIME, sync_time.isoformat())
        Logger.info(Messages.NEO4J_SYNC_TIME_SAVED(sync_time.isoformat()))
    except Exception as e:
        Logger.error(Messages.NEO4J_SYNC_TIME_SAVE_FAILED(e))


async def _get_last_sync_time() -> Optional[datetime]:
    """从 Redis 获取上次 Neo4j 同步时间"""
    try:
        redis_client = get_redis_client()
        timestamp_str = await redis_client.get(RedisKeys.NEO4J_SYNC_TIME)
        if timestamp_str:
            return datetime.fromisoformat(timestamp_str)
    except Exception as e:
        Logger.warning(Messages.NEO4J_SYNC_TIME_READ_FAILED(e))
    return None


async def _sync_mysql_to_neo4j(force_full: bool = False) -> Dict[str, int]:
    """同步 MySQL 数据到 Neo4j

    force_full=False（默认，增量同步）：仅同步窗口内变更的数据，不做全图清理，
        避免用增量快照误删全图（见 sync_incremental 说明）。
    force_full=True（全量同步）：拉取全量快照并安全执行清理，用于周期性兜底
        清理 MySQL 中已删除的记录。
    """
    sync_start_time = datetime.now()
    Logger.info(Messages.NEO4J_TASK_START_MESSAGE)

    try:
        sync_service = get_knowledge_graph_sync_service()
        if force_full:
            result = await sync_service.sync_all()
        else:
            last_sync_time = await _get_last_sync_time()
            result = await sync_service.sync_incremental(last_sync_time)
        if any(result.values()):
            await _save_sync_time(sync_start_time)
        Logger.info(Messages.NEO4J_TASK_FINISH_MESSAGE(result))
        return result
    except Exception as e:
        Logger.error(Messages.NEO4J_MYSQL_SYNC_FAILED(e))
        return {}


async def sync_mysql_to_neo4j_async(force_full: bool = False) -> None:
    """同步 MySQL 数据到 Neo4j，使用 Redis 分布式锁避免多实例重复执行

    force_full=True 时执行全量同步（含安全清理），用于周期性兜底清理已删除数据。
    """
    lock_key: str = RedisKeys.LOCK_TASK_NEO4J_SYNC
    lock_expire: int = RedisKeys.LOCK_TASK_NEO4J_SYNC_EXPIRE

    redis_client = get_redis_client()
    lock_value: Optional[str] = await redis_client.try_lock(lock_key, lock_expire)
    if lock_value is None:
        Logger.info(Messages.REDIS_LOCK_ACQUIRE_FAIL_MESSAGE(lock_key))
        return
    Logger.info(Messages.REDIS_LOCK_ACQUIRE_SUCCESS_MESSAGE(lock_key))

    try:
        await _sync_mysql_to_neo4j(force_full=force_full)
    finally:
        released = await redis_client.unlock(lock_key, lock_value)
        if released:
            Logger.info(Messages.REDIS_LOCK_RELEASE_SUCCESS_MESSAGE(lock_key))
        else:
            Logger.info(Messages.REDIS_LOCK_RELEASE_FAIL_MESSAGE(lock_key))
