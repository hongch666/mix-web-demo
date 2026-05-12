import asyncio
import hashlib
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set

from app.core.base import Constants, Logger
from app.core.db import SessionLocal, get_redis_client
from app.core.db.neo4j import get_neo4j_client
from sqlalchemy import text

_NEO4J_SYNC_TIME_KEY: str = "neo4j_sync:last_sync_time"


class KnowledgeGraphSyncService:
    """知识图谱同步服务：将 MySQL 业务数据同步到 Neo4j"""

    def __init__(self) -> None:
        self.logger = Logger
        self.client = get_neo4j_client()

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
        articles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        relations: List[Dict[str, Any]] = []
        for article in articles:
            article_id = article.get("id")
            tags = str(article.get("tags") or "")
            for tag_name in [item.strip() for item in tags.split(",") if item.strip()]:
                relations.append({"articleId": article_id, "tagName": tag_name})
        return relations

    def _fetch_rows(self, sql: str) -> List[Any]:
        with SessionLocal() as session:
            return list(session.execute(text(sql)).fetchall())

    def _build_incremental_sql(
        self,
        base_sql: str,
        timestamp_column: Optional[str],
        last_sync_time: Optional[datetime],
    ) -> str:
        if last_sync_time is None or not timestamp_column:
            return base_sql
        sync_time_text = last_sync_time.strftime("%Y-%m-%d %H:%M:%S")
        return Constants.NEO4J_SQL_INCREMENTAL_SUFFIX_FORMAT % (
            base_sql,
            timestamp_column,
            sync_time_text,
            timestamp_column,
        )

    def _fetch_all_users(
        self, last_sync_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        rows = self._fetch_rows(
            self._build_incremental_sql(
                Constants.NEO4J_SQL_SELECT_USERS,
                "update_at",
                last_sync_time,
            )
        )
        return [
            {
                "id": int(row[0]),
                "name": row[1] or "",
                "email": row[2] or "",
                "role": row[3] or "user",
                "img": row[4] or "",
                "signature": row[5] or "",
                "createdAt": self._format_datetime(row[6]),
                "updatedAt": self._format_datetime(row[7]),
            }
            for row in rows
        ]

    def _fetch_all_categories(
        self, last_sync_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        rows = self._fetch_rows(
            self._build_incremental_sql(
                Constants.NEO4J_SQL_SELECT_CATEGORIES,
                "update_time",
                last_sync_time,
            )
        )
        return [
            {
                "id": int(row[0]),
                "name": row[1] or "",
                "updatedAt": self._format_datetime(row[2]),
            }
            for row in rows
        ]

    def _fetch_all_sub_categories(
        self, last_sync_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        rows = self._fetch_rows(
            self._build_incremental_sql(
                Constants.NEO4J_SQL_SELECT_SUB_CATEGORIES,
                "update_time",
                last_sync_time,
            )
        )
        return [
            {
                "id": int(row[0]),
                "name": row[1] or "",
                "categoryId": int(row[2]) if row[2] is not None else None,
                "updatedAt": self._format_datetime(row[3]),
            }
            for row in rows
        ]

    def _fetch_all_articles(
        self, last_sync_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        rows = self._fetch_rows(
            self._build_incremental_sql(
                Constants.NEO4J_SQL_SELECT_ARTICLES,
                "update_at",
                last_sync_time,
            )
        )
        return [
            {
                "id": int(row[0]),
                "title": row[1] or "",
                "tags": row[2] or "",
                "status": str(row[3]) if row[3] is not None else "",
                "views": int(row[4] or 0),
                "userId": int(row[5]) if row[5] is not None else None,
                "subCategoryId": int(row[6]) if row[6] is not None else None,
                "createAt": self._format_datetime(row[7]),
                "updateAt": self._format_datetime(row[8]),
                "contentHash": self._compute_content_hash(row[1], row[9], row[2]),
                "updatedAt": self._format_datetime(row[8]),
            }
            for row in rows
        ]

    def _fetch_all_likes(
        self, last_sync_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        rows = self._fetch_rows(
            self._build_incremental_sql(
                Constants.NEO4J_SQL_SELECT_LIKES,
                "created_time",
                last_sync_time,
            )
        )
        return [
            {
                "userId": int(row[0]),
                "articleId": int(row[1]),
                "createdAt": self._format_datetime(row[2]),
            }
            for row in rows
        ]

    def _fetch_all_collects(
        self, last_sync_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        rows = self._fetch_rows(
            self._build_incremental_sql(
                Constants.NEO4J_SQL_SELECT_COLLECTS,
                "created_time",
                last_sync_time,
            )
        )
        return [
            {
                "userId": int(row[0]),
                "articleId": int(row[1]),
                "createdAt": self._format_datetime(row[2]),
            }
            for row in rows
        ]

    def _fetch_all_comments(
        self, last_sync_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        rows = self._fetch_rows(
            self._build_incremental_sql(
                Constants.NEO4J_SQL_SELECT_COMMENTS,
                "update_time",
                last_sync_time,
            )
        )
        return [
            {
                "commentId": int(row[0]),
                "userId": int(row[1]),
                "articleId": int(row[2]),
                "createdAt": self._format_datetime(row[3]),
            }
            for row in rows
        ]

    def _fetch_all_focus(
        self, last_sync_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        rows = self._fetch_rows(
            self._build_incremental_sql(
                Constants.NEO4J_SQL_SELECT_FOCUS,
                "created_time",
                last_sync_time,
            )
        )
        return [
            {
                "followerId": int(row[0]),
                "followedId": int(row[1]),
                "createdAt": self._format_datetime(row[2]),
            }
            for row in rows
        ]

    async def _ensure_schema(self) -> None:
        for cypher in Constants.NEO4J_CREATE_CONSTRAINTS:
            await self.client.run_write_query(cypher)

    async def _batch_write(
        self,
        rows: List[Dict[str, Any]],
        cypher: str,
        label: str,
        batch_size: int = 500,
    ) -> int:
        if not rows:
            self.logger.info(f"[知识图谱] 无 {label} 需要同步")
            return 0

        total = 0
        for start in range(0, len(rows), batch_size):
            batch = rows[start : start + batch_size]
            await self.client.run_write_query(cypher, {"rows": batch})
            total += len(batch)
            self.logger.info(f"[知识图谱] 已同步 {label}: {total}/{len(rows)}")
        return total

    async def _cleanup_write(
        self, cypher: str, params: Dict[str, Any], label: str
    ) -> int:
        summary = await self.client.run_write_query(cypher, params)
        deleted_count = self._extract_deleted_count(summary)
        self.logger.info(f"[知识图谱] 已清理 {label}: {deleted_count}")
        return deleted_count

    async def _has_graph_data(self) -> bool:
        records = await self.client.run_query(Constants.NEO4J_GRAPH_COUNT_CYPHER)
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
        """按 MySQL 当前完整快照删除 Neo4j 中已经不存在的节点和关系"""
        self.logger.info(Constants.NEO4J_CLEANUP_DELETED_DATA_START_MESSAGE)

        users = users if users is not None else self._fetch_all_users()
        categories = (
            categories if categories is not None else self._fetch_all_categories()
        )
        sub_categories = (
            sub_categories
            if sub_categories is not None
            else self._fetch_all_sub_categories()
        )
        articles = articles if articles is not None else self._fetch_all_articles()
        likes = likes if likes is not None else self._fetch_all_likes()
        collects = collects if collects is not None else self._fetch_all_collects()
        comments = comments if comments is not None else self._fetch_all_comments()
        focus = focus if focus is not None else self._fetch_all_focus()
        article_tag_relations = self._build_article_tag_relations(articles)

        cleanup_result: Dict[str, int] = {}

        cleanup_result["published_by"] = await self._cleanup_write(
            Constants.NEO4J_CLEANUP_PUBLISHED_BY_CYPHER,
            {
                "keys": [
                    self._build_relation_key(item["id"], item["userId"])
                    for item in articles
                    if item.get("userId") is not None
                ]
            },
            Constants.NEO4J_CLEANUP_LABEL_PUBLISHED_BY_RELATION,
        )

        cleanup_result["article_sub_category"] = await self._cleanup_write(
            Constants.NEO4J_CLEANUP_ARTICLE_SUB_CATEGORY_CYPHER,
            {
                "keys": [
                    self._build_relation_key(item["id"], item["subCategoryId"])
                    for item in articles
                    if item.get("subCategoryId") is not None
                ]
            },
            Constants.NEO4J_CLEANUP_LABEL_ARTICLE_SUB_CATEGORY_RELATION,
        )

        cleanup_result["sub_category_category"] = await self._cleanup_write(
            Constants.NEO4J_CLEANUP_SUB_CATEGORY_CATEGORY_CYPHER,
            {
                "keys": [
                    self._build_relation_key(item["id"], item["categoryId"])
                    for item in sub_categories
                    if item.get("categoryId") is not None
                ]
            },
            Constants.NEO4J_CLEANUP_LABEL_SUB_CATEGORY_CATEGORY_RELATION,
        )

        cleanup_result["tagged_as"] = await self._cleanup_write(
            Constants.NEO4J_CLEANUP_TAGGED_AS_CYPHER,
            {
                "keys": [
                    self._build_relation_key(item["articleId"], item["tagName"])
                    for item in article_tag_relations
                ]
            },
            Constants.NEO4J_CLEANUP_LABEL_TAGGED_AS_RELATION,
        )

        cleanup_result["likes"] = await self._cleanup_write(
            Constants.NEO4J_CLEANUP_LIKES_CYPHER,
            {
                "keys": [
                    self._build_relation_key(item["userId"], item["articleId"])
                    for item in likes
                ]
            },
            Constants.NEO4J_CLEANUP_LABEL_LIKE_RELATION,
        )

        cleanup_result["collects"] = await self._cleanup_write(
            Constants.NEO4J_CLEANUP_COLLECTS_CYPHER,
            {
                "keys": [
                    self._build_relation_key(item["userId"], item["articleId"])
                    for item in collects
                ]
            },
            Constants.NEO4J_CLEANUP_LABEL_COLLECT_RELATION,
        )

        cleanup_result["commented_on"] = await self._cleanup_write(
            Constants.NEO4J_CLEANUP_COMMENTED_ON_CYPHER,
            {
                "keys": [
                    self._build_relation_key(
                        item["commentId"], item["userId"], item["articleId"]
                    )
                    for item in comments
                ]
            },
            Constants.NEO4J_CLEANUP_LABEL_COMMENT_RELATION,
        )

        cleanup_result["follows"] = await self._cleanup_write(
            Constants.NEO4J_CLEANUP_FOLLOWS_CYPHER,
            {
                "keys": [
                    self._build_relation_key(item["followerId"], item["followedId"])
                    for item in focus
                ]
            },
            Constants.NEO4J_CLEANUP_LABEL_FOLLOW_RELATION,
        )

        cleanup_result["articles"] = await self._cleanup_write(
            Constants.NEO4J_CLEANUP_ARTICLES_CYPHER,
            {"ids": [item["id"] for item in articles]},
            Constants.NEO4J_CLEANUP_LABEL_ARTICLE,
        )

        cleanup_result["users"] = await self._cleanup_write(
            Constants.NEO4J_CLEANUP_USERS_CYPHER,
            {"ids": [item["id"] for item in users]},
            Constants.NEO4J_CLEANUP_LABEL_USER,
        )

        cleanup_result["sub_categories"] = await self._cleanup_write(
            Constants.NEO4J_CLEANUP_SUB_CATEGORIES_CYPHER,
            {"ids": [item["id"] for item in sub_categories]},
            Constants.NEO4J_CLEANUP_LABEL_SUB_CATEGORY,
        )

        cleanup_result["categories"] = await self._cleanup_write(
            Constants.NEO4J_CLEANUP_CATEGORIES_CYPHER,
            {"ids": [item["id"] for item in categories]},
            Constants.NEO4J_CLEANUP_LABEL_CATEGORY,
        )

        cleanup_result["tags"] = await self._cleanup_write(
            Constants.NEO4J_CLEANUP_TAGS_CYPHER,
            {
                "names": sorted(
                    {
                        item["tagName"]
                        for item in article_tag_relations
                        if item.get("tagName")
                    }
                )
            },
            Constants.NEO4J_CLEANUP_LABEL_TAG,
        )

        cleanup_result["total"] = sum(cleanup_result.values())
        self.logger.info(f"[知识图谱] 删除同步清理完成: {cleanup_result}")
        return cleanup_result

    async def sync_all(self) -> Dict[str, int]:
        """全量同步 MySQL 数据到 Neo4j"""
        self.logger.info(Constants.NEO4J_SYNC_START_MESSAGE)
        await self._ensure_schema()

        result: Dict[str, int] = {}

        users = self._fetch_all_users()
        result["users"] = await self._batch_write(
            users, Constants.NEO4J_MERGE_USERS_CYPHER, Constants.NEO4J_LABEL_USER
        )

        categories = self._fetch_all_categories()
        result["categories"] = await self._batch_write(
            categories,
            Constants.NEO4J_MERGE_CATEGORIES_CYPHER,
            Constants.NEO4J_LABEL_CATEGORY,
        )

        sub_categories = self._fetch_all_sub_categories()
        result["sub_categories"] = await self._batch_write(
            sub_categories,
            Constants.NEO4J_MERGE_SUB_CATEGORIES_CYPHER,
            Constants.NEO4J_LABEL_SUB_CATEGORY,
        )

        articles = self._fetch_all_articles()
        result["articles"] = await self._batch_write(
            articles,
            Constants.NEO4J_MERGE_ARTICLES_CYPHER,
            Constants.NEO4J_LABEL_ARTICLE,
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
            tags, Constants.NEO4J_MERGE_TAGS_CYPHER, Constants.NEO4J_LABEL_TAG
        )

        sub_category_relations = [
            {"subCategoryId": item["id"], "categoryId": item["categoryId"]}
            for item in sub_categories
            if item.get("categoryId") is not None
        ]
        result["sub_category_belongs_to_category"] = await self._batch_write(
            sub_category_relations,
            Constants.NEO4J_MERGE_SUB_CATEGORY_TO_CATEGORY_CYPHER,
            Constants.NEO4J_LABEL_SUB_CATEGORY_RELATION,
        )

        article_sub_relations = [
            {"articleId": item["id"], "subCategoryId": item["subCategoryId"]}
            for item in articles
            if item.get("subCategoryId") is not None
        ]
        result["belongs_to"] = await self._batch_write(
            article_sub_relations,
            Constants.NEO4J_MERGE_ARTICLE_TO_SUB_CATEGORY_CYPHER,
            Constants.NEO4J_LABEL_ARTICLE_SUB_CATEGORY_RELATION,
        )

        article_user_relations = [
            {"articleId": item["id"], "userId": item["userId"]}
            for item in articles
            if item.get("userId") is not None
        ]
        result["published_by"] = await self._batch_write(
            article_user_relations,
            Constants.NEO4J_MERGE_PUBLISHED_BY_CYPHER,
            Constants.NEO4J_LABEL_ARTICLE_AUTHOR_RELATION,
        )

        result["tagged_as"] = await self._batch_write(
            article_tag_relations,
            Constants.NEO4J_MERGE_TAGGED_AS_CYPHER,
            Constants.NEO4J_LABEL_ARTICLE_TAG_RELATION,
        )

        likes = self._fetch_all_likes()
        result["likes"] = await self._batch_write(
            likes,
            Constants.NEO4J_MERGE_LIKES_CYPHER,
            Constants.NEO4J_LABEL_LIKE_RELATION,
        )

        collects = self._fetch_all_collects()
        result["collects"] = await self._batch_write(
            collects,
            Constants.NEO4J_MERGE_COLLECTS_CYPHER,
            Constants.NEO4J_LABEL_COLLECT_RELATION,
        )

        comments = self._fetch_all_comments()
        result["commented_on"] = await self._batch_write(
            comments,
            Constants.NEO4J_MERGE_COMMENTED_ON_CYPHER,
            Constants.NEO4J_LABEL_COMMENT_RELATION,
        )

        focus = self._fetch_all_focus()
        result["follows"] = await self._batch_write(
            focus,
            Constants.NEO4J_MERGE_FOLLOWS_CYPHER,
            Constants.NEO4J_LABEL_FOLLOW_RELATION,
        )

        cleanup_result = await self._cleanup_deleted_graph_data(
            users=users,
            categories=categories,
            sub_categories=sub_categories,
            articles=articles,
            likes=likes,
            collects=collects,
            comments=comments,
            focus=focus,
        )
        result.update(
            {f"cleanup_{key}": value for key, value in cleanup_result.items()}
        )

        self.logger.info(f"[知识图谱] 全量同步完成: {result}")
        return result

    async def sync_incremental(
        self, last_sync_time: Optional[datetime]
    ) -> Dict[str, int]:
        """增量同步 MySQL 数据到 Neo4j，如果图为空则退化为全量同步"""
        await self._ensure_schema()

        has_graph_data = await self._has_graph_data()
        if not has_graph_data:
            self.logger.info(Constants.NEO4J_GRAPH_EMPTY_FULL_SYNC_MESSAGE)
            return await self.sync_all()

        if last_sync_time is None:
            self.logger.info(Constants.NEO4J_GRAPH_EMPTY_FULL_SYNC_MESSAGE)
            return await self.sync_all()

        self.logger.info(Constants.NEO4J_INCREMENTAL_SYNC_START_MESSAGE)

        result: Dict[str, int] = {}

        users = self._fetch_all_users(last_sync_time)
        result["users"] = await self._batch_write(
            users, Constants.NEO4J_MERGE_USERS_CYPHER, Constants.NEO4J_LABEL_USER
        )

        categories = self._fetch_all_categories(last_sync_time)
        result["categories"] = await self._batch_write(
            categories,
            Constants.NEO4J_MERGE_CATEGORIES_CYPHER,
            Constants.NEO4J_LABEL_CATEGORY,
        )

        sub_categories = self._fetch_all_sub_categories(last_sync_time)
        result["sub_categories"] = await self._batch_write(
            sub_categories,
            Constants.NEO4J_MERGE_SUB_CATEGORIES_CYPHER,
            Constants.NEO4J_LABEL_SUB_CATEGORY,
        )

        articles = self._fetch_all_articles(last_sync_time)
        result["articles"] = await self._batch_write(
            articles,
            Constants.NEO4J_MERGE_ARTICLES_CYPHER,
            Constants.NEO4J_LABEL_ARTICLE,
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
            tags, Constants.NEO4J_MERGE_TAGS_CYPHER, Constants.NEO4J_LABEL_TAG
        )

        sub_category_relations = [
            {"subCategoryId": item["id"], "categoryId": item["categoryId"]}
            for item in sub_categories
            if item.get("categoryId") is not None
        ]
        result["sub_category_belongs_to_category"] = await self._batch_write(
            sub_category_relations,
            Constants.NEO4J_MERGE_SUB_CATEGORY_TO_CATEGORY_CYPHER,
            Constants.NEO4J_LABEL_SUB_CATEGORY_RELATION,
        )

        article_sub_relations = [
            {"articleId": item["id"], "subCategoryId": item["subCategoryId"]}
            for item in articles
            if item.get("subCategoryId") is not None
        ]
        result["belongs_to"] = await self._batch_write(
            article_sub_relations,
            Constants.NEO4J_MERGE_ARTICLE_TO_SUB_CATEGORY_CYPHER,
            Constants.NEO4J_LABEL_ARTICLE_SUB_CATEGORY_RELATION,
        )

        article_user_relations = [
            {"articleId": item["id"], "userId": item["userId"]}
            for item in articles
            if item.get("userId") is not None
        ]
        result["published_by"] = await self._batch_write(
            article_user_relations,
            Constants.NEO4J_MERGE_PUBLISHED_BY_CYPHER,
            Constants.NEO4J_LABEL_ARTICLE_AUTHOR_RELATION,
        )

        result["tagged_as"] = await self._batch_write(
            article_tag_relations,
            Constants.NEO4J_MERGE_TAGGED_AS_CYPHER,
            Constants.NEO4J_LABEL_ARTICLE_TAG_RELATION,
        )

        likes = self._fetch_all_likes(last_sync_time)
        result["likes"] = await self._batch_write(
            likes,
            Constants.NEO4J_MERGE_LIKES_CYPHER,
            Constants.NEO4J_LABEL_LIKE_RELATION,
        )

        collects = self._fetch_all_collects(last_sync_time)
        result["collects"] = await self._batch_write(
            collects,
            Constants.NEO4J_MERGE_COLLECTS_CYPHER,
            Constants.NEO4J_LABEL_COLLECT_RELATION,
        )

        comments = self._fetch_all_comments(last_sync_time)
        result["commented_on"] = await self._batch_write(
            comments,
            Constants.NEO4J_MERGE_COMMENTED_ON_CYPHER,
            Constants.NEO4J_LABEL_COMMENT_RELATION,
        )

        focus = self._fetch_all_focus(last_sync_time)
        result["follows"] = await self._batch_write(
            focus,
            Constants.NEO4J_MERGE_FOLLOWS_CYPHER,
            Constants.NEO4J_LABEL_FOLLOW_RELATION,
        )

        cleanup_result = await self._cleanup_deleted_graph_data()
        result.update(
            {f"cleanup_{key}": value for key, value in cleanup_result.items()}
        )

        if not any(result.values()):
            self.logger.info(Constants.NEO4J_NO_INCREMENTAL_DATA_MESSAGE)

        return result


@lru_cache
def get_knowledge_graph_sync_service() -> KnowledgeGraphSyncService:
    """获取知识图谱同步服务单例"""
    return KnowledgeGraphSyncService()


def _run_redis_coro(coro: Any) -> Any:
    """在同步线程中执行 Redis 协程"""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    raise RuntimeError(Constants.REDIS_COROUTINE_SYNC_EXECUTION_ERROR)


def _save_sync_time(sync_time: datetime) -> None:
    """将 Neo4j 同步时间保存到 Redis"""
    try:
        redis_client = get_redis_client()
        _run_redis_coro(redis_client.set(_NEO4J_SYNC_TIME_KEY, sync_time.isoformat()))
        Logger.info(f"[知识图谱] 已保存同步时间戳到 Redis: {sync_time.isoformat()}")
    except Exception as e:
        Logger.error(f"[知识图谱] 保存同步时间戳到 Redis 失败: {e}")


def _get_last_sync_time() -> Optional[datetime]:
    """从 Redis 获取上次 Neo4j 同步时间"""
    try:
        redis_client = get_redis_client()
        timestamp_str = _run_redis_coro(redis_client.get(_NEO4J_SYNC_TIME_KEY))
        if timestamp_str:
            return datetime.fromisoformat(timestamp_str)
    except Exception as e:
        Logger.warning(f"从 Redis 读取 Neo4j 同步时间戳失败: {e}")
    return None


def _sync_mysql_to_neo4j() -> Dict[str, int]:
    """同步线程入口：优先增量同步 MySQL 数据到 Neo4j"""
    sync_start_time = datetime.now()
    Logger.info(Constants.NEO4J_TASK_START_MESSAGE)

    try:
        sync_service = get_knowledge_graph_sync_service()
        last_sync_time = _get_last_sync_time()
        result = asyncio.run(sync_service.sync_incremental(last_sync_time))
        if any(result.values()):
            _save_sync_time(sync_start_time)
        Logger.info(Constants.NEO4J_TASK_FINISH_MESSAGE % result)
        return result
    except Exception as e:
        Logger.error(f"[知识图谱任务] MySQL 到 Neo4j 同步失败: {e}")
        return {}


async def sync_mysql_to_neo4j_async() -> None:
    """同步 MySQL 数据到 Neo4j，使用 Redis 分布式锁避免多实例重复执行"""
    lock_key: str = Constants.LOCK_TASK_NEO4J_SYNC
    lock_expire: int = Constants.LOCK_TASK_NEO4J_SYNC_EXPIRE

    redis_client = get_redis_client()
    lock_value: Optional[str] = await redis_client.try_lock(lock_key, lock_expire)
    if lock_value is None:
        Logger.info(Constants.REDIS_LOCK_ACQUIRE_FAIL_MESSAGE % lock_key)
        return
    Logger.info(Constants.REDIS_LOCK_ACQUIRE_SUCCESS_MESSAGE % lock_key)

    try:
        await asyncio.to_thread(_sync_mysql_to_neo4j)
    finally:
        released = await redis_client.unlock(lock_key, lock_value)
        if released:
            Logger.info(Constants.REDIS_LOCK_RELEASE_SUCCESS_MESSAGE % lock_key)
        else:
            Logger.info(Constants.REDIS_LOCK_RELEASE_FAIL_MESSAGE % lock_key)
