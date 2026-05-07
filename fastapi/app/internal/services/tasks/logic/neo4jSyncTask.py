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

    CREATE_CONSTRAINTS: List[str] = [
        "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
        "CREATE CONSTRAINT category_id_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT sub_category_id_unique IF NOT EXISTS FOR (s:SubCategory) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT article_id_unique IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE",
        "CREATE CONSTRAINT tag_name_unique IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE",
    ]

    MERGE_USERS: str = """
        UNWIND $rows AS row
        MERGE (u:User {id: row.id})
        SET u.name = row.name,
            u.email = row.email,
            u.role = row.role,
            u.img = row.img,
            u.signature = row.signature,
            u.updatedAt = row.updatedAt
    """
    MERGE_CATEGORIES: str = """
        UNWIND $rows AS row
        MERGE (c:Category {id: row.id})
        SET c.name = row.name,
            c.updatedAt = row.updatedAt
    """
    MERGE_SUB_CATEGORIES: str = """
        UNWIND $rows AS row
        MERGE (s:SubCategory {id: row.id})
        SET s.name = row.name,
            s.categoryId = row.categoryId,
            s.updatedAt = row.updatedAt
    """
    MERGE_ARTICLES: str = """
        UNWIND $rows AS row
        MERGE (a:Article {id: row.id})
        SET a.title = row.title,
            a.tags = row.tags,
            a.status = row.status,
            a.views = row.views,
            a.createAt = row.createAt,
            a.updateAt = row.updateAt,
            a.contentHash = row.contentHash,
            a.updatedAt = row.updatedAt
    """
    MERGE_TAGS: str = """
        UNWIND $rows AS row
        MERGE (t:Tag {name: row.name})
    """
    MERGE_SUB_CATEGORY_BELONGS_TO_CATEGORY: str = """
        UNWIND $rows AS row
        MATCH (s:SubCategory {id: row.subCategoryId})
        MATCH (c:Category {id: row.categoryId})
        MERGE (s)-[:BELONGS_TO_CATEGORY]->(c)
    """
    MERGE_ARTICLE_BELONGS_TO: str = """
        UNWIND $rows AS row
        MATCH (a:Article {id: row.articleId})
        MATCH (s:SubCategory {id: row.subCategoryId})
        MERGE (a)-[:BELONGS_TO]->(s)
    """
    MERGE_PUBLISHED_BY: str = """
        UNWIND $rows AS row
        MATCH (a:Article {id: row.articleId})
        MATCH (u:User {id: row.userId})
        MERGE (a)-[:PUBLISHED_BY]->(u)
    """
    MERGE_TAGGED_AS: str = """
        UNWIND $rows AS row
        MATCH (a:Article {id: row.articleId})
        MATCH (t:Tag {name: row.tagName})
        MERGE (a)-[:TAGGED_AS]->(t)
    """
    MERGE_LIKES: str = """
        UNWIND $rows AS row
        MATCH (u:User {id: row.userId})
        MATCH (a:Article {id: row.articleId})
        MERGE (u)-[r:LIKES]->(a)
        SET r.createdAt = row.createdAt
    """
    MERGE_COLLECTS: str = """
        UNWIND $rows AS row
        MATCH (u:User {id: row.userId})
        MATCH (a:Article {id: row.articleId})
        MERGE (u)-[r:COLLECTS]->(a)
        SET r.createdAt = row.createdAt
    """
    MERGE_COMMENTED_ON: str = """
        UNWIND $rows AS row
        MATCH (u:User {id: row.userId})
        MATCH (a:Article {id: row.articleId})
        MERGE (u)-[r:COMMENTED_ON {commentId: row.commentId}]->(a)
        SET r.createdAt = row.createdAt
    """
    MERGE_FOLLOWS: str = """
        UNWIND $rows AS row
        MATCH (u1:User {id: row.followerId})
        MATCH (u2:User {id: row.followedId})
        MERGE (u1)-[r:FOLLOWS]->(u2)
        SET r.createdAt = row.createdAt
    """

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

    def _fetch_rows(self, sql: str) -> List[Any]:
        with SessionLocal() as session:
            return list(session.execute(text(sql)).fetchall())

    def _fetch_all_users(self) -> List[Dict[str, Any]]:
        rows = self._fetch_rows(
            "SELECT id, name, email, role, img, signature FROM user"
        )
        return [
            {
                "id": int(row[0]),
                "name": row[1] or "",
                "email": row[2] or "",
                "role": row[3] or "user",
                "img": row[4] or "",
                "signature": row[5] or "",
                "updatedAt": datetime.now().isoformat(),
            }
            for row in rows
        ]

    def _fetch_all_categories(self) -> List[Dict[str, Any]]:
        rows = self._fetch_rows("SELECT id, name, update_time FROM category")
        return [
            {
                "id": int(row[0]),
                "name": row[1] or "",
                "updatedAt": self._format_datetime(row[2]),
            }
            for row in rows
        ]

    def _fetch_all_sub_categories(self) -> List[Dict[str, Any]]:
        rows = self._fetch_rows(
            "SELECT id, name, category_id, update_time FROM sub_category"
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

    def _fetch_all_articles(self) -> List[Dict[str, Any]]:
        rows = self._fetch_rows(
            "SELECT id, title, tags, status, views, user_id, sub_category_id, "
            "create_at, update_at, content FROM articles"
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
                "updatedAt": datetime.now().isoformat(),
            }
            for row in rows
        ]

    def _fetch_all_likes(self) -> List[Dict[str, Any]]:
        rows = self._fetch_rows("SELECT user_id, article_id, created_time FROM likes")
        return [
            {
                "userId": int(row[0]),
                "articleId": int(row[1]),
                "createdAt": self._format_datetime(row[2]),
            }
            for row in rows
        ]

    def _fetch_all_collects(self) -> List[Dict[str, Any]]:
        rows = self._fetch_rows(
            "SELECT user_id, article_id, created_time FROM collects"
        )
        return [
            {
                "userId": int(row[0]),
                "articleId": int(row[1]),
                "createdAt": self._format_datetime(row[2]),
            }
            for row in rows
        ]

    def _fetch_all_comments(self) -> List[Dict[str, Any]]:
        rows = self._fetch_rows(
            "SELECT id, user_id, article_id, create_time FROM comments"
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

    def _fetch_all_focus(self) -> List[Dict[str, Any]]:
        rows = self._fetch_rows("SELECT user_id, focus_id, created_time FROM focus")
        return [
            {
                "followerId": int(row[0]),
                "followedId": int(row[1]),
                "createdAt": self._format_datetime(row[2]),
            }
            for row in rows
        ]

    async def _ensure_schema(self) -> None:
        for cypher in self.CREATE_CONSTRAINTS:
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

    async def sync_all(self) -> Dict[str, int]:
        """全量同步 MySQL 数据到 Neo4j"""
        self.logger.info(Constants.NEO4J_SYNC_START_MESSAGE)
        await self._ensure_schema()

        result: Dict[str, int] = {}

        users = self._fetch_all_users()
        result["users"] = await self._batch_write(
            users, self.MERGE_USERS, Constants.NEO4J_LABEL_USER
        )

        categories = self._fetch_all_categories()
        result["categories"] = await self._batch_write(
            categories, self.MERGE_CATEGORIES, Constants.NEO4J_LABEL_CATEGORY
        )

        sub_categories = self._fetch_all_sub_categories()
        result["sub_categories"] = await self._batch_write(
            sub_categories,
            self.MERGE_SUB_CATEGORIES,
            Constants.NEO4J_LABEL_SUB_CATEGORY,
        )

        articles = self._fetch_all_articles()
        result["articles"] = await self._batch_write(
            articles, self.MERGE_ARTICLES, Constants.NEO4J_LABEL_ARTICLE
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
            tags, self.MERGE_TAGS, Constants.NEO4J_LABEL_TAG
        )

        sub_category_relations = [
            {"subCategoryId": item["id"], "categoryId": item["categoryId"]}
            for item in sub_categories
            if item.get("categoryId") is not None
        ]
        result["sub_category_belongs_to_category"] = await self._batch_write(
            sub_category_relations,
            self.MERGE_SUB_CATEGORY_BELONGS_TO_CATEGORY,
            Constants.NEO4J_LABEL_SUB_CATEGORY_RELATION,
        )

        article_sub_relations = [
            {"articleId": item["id"], "subCategoryId": item["subCategoryId"]}
            for item in articles
            if item.get("subCategoryId") is not None
        ]
        result["belongs_to"] = await self._batch_write(
            article_sub_relations,
            self.MERGE_ARTICLE_BELONGS_TO,
            Constants.NEO4J_LABEL_ARTICLE_SUB_CATEGORY_RELATION,
        )

        article_user_relations = [
            {"articleId": item["id"], "userId": item["userId"]}
            for item in articles
            if item.get("userId") is not None
        ]
        result["published_by"] = await self._batch_write(
            article_user_relations,
            self.MERGE_PUBLISHED_BY,
            Constants.NEO4J_LABEL_ARTICLE_AUTHOR_RELATION,
        )

        result["tagged_as"] = await self._batch_write(
            article_tag_relations,
            self.MERGE_TAGGED_AS,
            Constants.NEO4J_LABEL_ARTICLE_TAG_RELATION,
        )

        likes = self._fetch_all_likes()
        result["likes"] = await self._batch_write(
            likes, self.MERGE_LIKES, Constants.NEO4J_LABEL_LIKE_RELATION
        )

        collects = self._fetch_all_collects()
        result["collects"] = await self._batch_write(
            collects, self.MERGE_COLLECTS, Constants.NEO4J_LABEL_COLLECT_RELATION
        )

        comments = self._fetch_all_comments()
        result["commented_on"] = await self._batch_write(
            comments, self.MERGE_COMMENTED_ON, Constants.NEO4J_LABEL_COMMENT_RELATION
        )

        focus = self._fetch_all_focus()
        result["follows"] = await self._batch_write(
            focus, self.MERGE_FOLLOWS, Constants.NEO4J_LABEL_FOLLOW_RELATION
        )

        self.logger.info(f"[知识图谱] 全量同步完成: {result}")
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


def _sync_mysql_to_neo4j() -> Dict[str, int]:
    """同步线程入口：全量同步 MySQL 数据到 Neo4j"""
    sync_start_time = datetime.now()
    Logger.info(Constants.NEO4J_TASK_START_MESSAGE)

    try:
        sync_service = get_knowledge_graph_sync_service()
        result = asyncio.run(sync_service.sync_all())
        _save_sync_time(sync_start_time)
        Logger.info(f"[知识图谱任务] MySQL 到 Neo4j 全量同步完成: {result}")
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
